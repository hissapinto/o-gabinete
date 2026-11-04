"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/carga.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Ultima etapa do pipeline. Grava no PostgreSQL tudo que a versao web le:
    os dados da Camara (deputados, proposicoes, votacoes, os vinculos entre
    votacao e proposicao, e os votos individuais) e os resultados do calculo
    (execucao, concordancia entre pares, arestas do grafo e a posicao x/y de
    cada vertice no desenho, calculada pelo layout.py).

    Reaproveita as funcoes de similaridade.py e gerar_grafo.py em vez de
    recalcular, de modo que as arestas gravadas no banco sejam exatamente as
    mesmas do dados/grafo.txt que a aplicacao de terminal le.

    Tudo acontece em uma transacao unica, e na ordem que as chaves
    estrangeiras exigem: se qualquer etapa falhar, o banco fica como estava.
    Rodar de novo nao duplica dados -- as votacoes do ano sao substituidas, e
    cada carga registra uma execucao nova em app.execucao com os parametros
    usados, o que permite comparar versoes diferentes do grafo.

    Idempotente: se a execucao mais recente do ano ja tem o layout gravado,
    a carga termina sem baixar nada. FORCAR_CARGA=1 recarrega mesmo assim.
    Le o banco de DATABASE_URL quando ela existe (servico carga do compose,
    ou o Neon com sslmode=require); senao, das variaveis POSTGRES_* do .env.

Historico de alteracoes:
    07/10/2026 - Kaique - Criacao.
    04/11/2026 - Caio - Grava em app.posicao o layout de cada vertice, na
                        mesma execucao das arestas.
    04/11/2026 - Caio - Conexao por DATABASE_URL, carga pulada quando o ano
                        ja esta carregado (FORCAR_CARGA) e erro claro no log.
"""

import os
import sys

import pandas as pd
import psycopg

from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar_dados_brutos
from processamento import ler_csv_camara, votacoes_de_merito
from similaridade import MINIMO_VOTACOES_EM_COMUM, matriz_de_votos, concordancia, pares_com_concordancia
from gerar_grafo import K_VIZINHOS, CONCORDANCIA_MINIMA, descartar_sem_par, montar_rotulos, montar_grafo
from layout import calcular_layout


def ler_configuracao():
    """Le o .env da raiz; variaveis de ambiente ja definidas tem prioridade."""
    config = {}
    arquivo = RAIZ / '.env'
    if arquivo.exists():
        for linha in arquivo.read_text(encoding='utf-8').splitlines():
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                chave, valor = linha.split('=', 1)
                config[chave.strip()] = valor.strip()
    config.update({k: v for k, v in os.environ.items() if k.startswith('POSTGRES_')})
    return config


def conectar():
    """
    DATABASE_URL tem prioridade: e o que o compose passa e o que se usa contra
    o Neon (a URL ja traz o sslmode=require). Sem ela, monta a conexao com as
    POSTGRES_* do .env, para a execucao manual contra o banco local.
    """
    url = os.environ.get('DATABASE_URL')
    if url:
        return psycopg.connect(url)
    config = ler_configuracao()
    return psycopg.connect(
        host=config.get('POSTGRES_HOST', 'localhost'),
        port=config.get('POSTGRES_PORT', '5432'),
        dbname=config['POSTGRES_DB'],
        user=config['POSTGRES_USER'],
        password=config.get('POSTGRES_PASSWORD', ''),
    )


def forcar_carga():
    """FORCAR_CARGA=1 (ou true/sim) recarrega mesmo com o ano ja carregado."""
    return os.environ.get('FORCAR_CARGA', '').strip().lower() in ('1', 'true', 'sim', 'yes')


def carga_existente(conexao, ano):
    """
    (execucao_id, posicoes) da execucao mais recente do ano, se ela ja tem o
    layout gravado; senao None. Como a carga roda numa transacao so, execucao
    gravada e execucao completa. O layout entra na conta porque uma execucao
    anterior a app.posicao deixaria a rota do grafo sem posicoes.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.execucao_id, count(p.deputado_id) AS posicoes
            FROM app.execucao e
            LEFT JOIN app.posicao p USING (execucao_id)
            WHERE e.execucao_id = (
                SELECT max(execucao_id) FROM app.execucao
                WHERE ano_inicio = %(ano)s AND ano_fim = %(ano)s
            )
            GROUP BY e.execucao_id
            """,
            {'ano': ano},
        )
        linha = cursor.fetchone()
    if linha is None or linha[1] == 0:
        return None
    return linha


def sem_nulos(df):
    """Troca NaN por None, que o psycopg grava como NULL."""
    return df.astype(object).where(df.notna(), None)


def deputados_do_ano(df_votos):
    """Um registro por deputado, com o partido do voto mais recente do ano."""
    df = df_votos.sort_values('dataHoraVoto').drop_duplicates('deputado_id', keep='last')
    df = df[['deputado_id', 'deputado_nome', 'deputado_siglaPartido', 'deputado_siglaUf', 'deputado_urlFoto']]
    return sem_nulos(df)


def votacoes_do_ano(pasta_brutos, ids):
    """Votacoes de merito do ano, com data, orgao e descricao."""
    df = ler_csv_camara(pasta_brutos / f'votacoes-{ANO_REFERENCIA}.csv')
    df = df[df['id'].isin(ids)]
    df = df.assign(data=pd.to_datetime(df['data']).dt.date)
    return sem_nulos(df[['id', 'data', 'siglaOrgao', 'descricao']])


def proposicoes_das_votacoes(pasta_brutos, ids):
    """Proposicoes afetadas pelas votacoes e o vinculo entre as duas."""
    df = ler_csv_camara(pasta_brutos / f'votacoesProposicoes-{ANO_REFERENCIA}.csv')
    df = df[df['idVotacao'].isin(ids)]
    proposicoes = df.drop_duplicates('proposicao_id')[
        ['proposicao_id', 'proposicao_siglaTipo', 'proposicao_numero', 'proposicao_ano', 'proposicao_ementa']
    ]
    vinculos = df[['idVotacao', 'proposicao_id']].drop_duplicates()
    return sem_nulos(proposicoes), sem_nulos(vinculos)


def votos_das_votacoes(df_votos, ids):
    """Voto de cada deputado, com o partido que ele tinha no dia."""
    df = df_votos[df_votos['idVotacao'].isin(ids)]
    return sem_nulos(df[['idVotacao', 'deputado_id', 'voto', 'deputado_siglaPartido']])


def calcular_resultados(df_votos, ids, deputados):
    """
    Concordancia de todos os pares validos, arestas do grafo e posicao de cada
    vertice, pelas regras do similaridade.py, do gerar_grafo.py e do layout.py.
    As arestas passam pelo montar_grafo, na mesma ordem de vertices do
    grafo.txt, para o banco ter as mesmas arestas; o layout recebe essa mesma
    ordem e o peso inteiro, entao sai o mesmo desenho do prototipo de IHC.
    Os pares vem sempre com o menor deputado_id em deputado_a.
    """
    matriz = matriz_de_votos(df_votos[df_votos['idVotacao'].isin(ids)])
    pares = pares_com_concordancia(matriz)

    C = concordancia(matriz).to_numpy()
    ids_grafo, C, descartados = descartar_sem_par(matriz.index.to_numpy(), C)
    rotulos = montar_rotulos(ids_grafo, deputados)
    ids_grafo, rotulos, arestas_por_vertice = montar_grafo(ids_grafo, C, rotulos)

    # o grafo usa a posicao do vertice; o banco usa o deputado_id real
    linhas = []
    for (v, w), peso in arestas_por_vertice.items():
        deputado_a = min(ids_grafo[v], ids_grafo[w])
        deputado_b = max(ids_grafo[v], ids_grafo[w])
        linhas.append((deputado_a, deputado_b, peso))
    arestas = pd.DataFrame(linhas, columns=['deputado_a', 'deputado_b', 'peso'])

    partidos = deputados.set_index('deputado_id')['deputado_siglaPartido'].to_dict()
    layout = calcular_layout(
        ids_grafo, partidos,
        {(a, b): peso for a, b, peso in linhas})
    posicoes = pd.DataFrame(
        [(deputado_id, x, y) for deputado_id, (x, y) in layout.items()],
        columns=['deputado_id', 'x', 'y'])

    return pares, arestas, posicoes


def carregar_deputados(conexao, df):
    """Insere ou atualiza os deputados em lote."""
    with conexao.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO app.deputado (deputado_id, nome, sigla_partido, sigla_uf, url_foto)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (deputado_id) DO UPDATE SET
                nome          = EXCLUDED.nome,
                sigla_partido = EXCLUDED.sigla_partido,
                sigla_uf      = EXCLUDED.sigla_uf,
                url_foto      = EXCLUDED.url_foto
            """,
            [tuple(linha) for linha in df.itertuples(index=False)],
        )
    return len(df)


def carregar_proposicoes(conexao, df):
    """Insere ou atualiza as proposicoes; a mesma pode ser votada em varios anos."""
    with conexao.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO app.proposicao (proposicao_id, sigla_tipo, numero, ano, ementa)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (proposicao_id) DO UPDATE SET
                sigla_tipo = EXCLUDED.sigla_tipo,
                numero     = EXCLUDED.numero,
                ano        = EXCLUDED.ano,
                ementa     = EXCLUDED.ementa
            """,
            [tuple(linha) for linha in df.itertuples(index=False)],
        )
    return len(df)


def copiar(cursor, comando, df):
    """Grava o DataFrame com COPY, bem mais rapido que INSERT linha a linha."""
    with cursor.copy(comando) as copia:
        for linha in df.itertuples(index=False):
            copia.write_row(linha)


def carregar_votacoes(conexao, votacoes, vinculos, votos):
    """
    Substitui as votacoes do ano. O DELETE leva junto os votos e os vinculos
    (ON DELETE CASCADE), entao rodar a carga de novo nao duplica nada e
    votacoes que deixaram de passar no filtro de merito saem do banco.
    """
    with conexao.cursor() as cursor:
        cursor.execute('DELETE FROM app.votacao WHERE ano = %s', (ANO_REFERENCIA,))
        copiar(cursor, 'COPY app.votacao (votacao_id, data, sigla_orgao, descricao) FROM STDIN', votacoes)
        copiar(cursor, 'COPY app.votacao_proposicao (votacao_id, proposicao_id) FROM STDIN', vinculos)
        copiar(cursor, 'COPY app.voto (votacao_id, deputado_id, voto, sigla_partido) FROM STDIN', votos)
    return len(votacoes), len(votos)


def atualizar_partido_atual(conexao):
    """
    Recalcula o partido atual de cada deputado pelo voto mais recente gravado,
    de qualquer ano. Assim a ordem em que os anos sao carregados nao importa.
    Deputados sem voto de merito ficam com o partido gravado pelo upsert.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app.deputado d
            SET sigla_partido = recente.sigla_partido
            FROM (
                SELECT DISTINCT ON (vo.deputado_id) vo.deputado_id, vo.sigla_partido
                FROM app.voto vo
                JOIN app.votacao v USING (votacao_id)
                ORDER BY vo.deputado_id, v.data DESC, vo.votacao_id DESC
            ) recente
            WHERE d.deputado_id = recente.deputado_id
              AND d.sigla_partido IS DISTINCT FROM recente.sigla_partido
            """
        )
        return cursor.rowcount


def carregar_resultados(conexao, pares, arestas, posicoes):
    """
    Cria uma execucao nova do ano, com os parametros usados, e grava a
    concordancia dos pares, as arestas e a posicao de cada vertice dela. A
    posicao fica na mesma execucao das arestas, para as duas nunca virem de
    cargas diferentes. As execucoes antigas ficam
    guardadas: rodar a carga de novo cria outra, sem apagar nada.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO app.execucao (ano_inicio, ano_fim, minimo_votacoes_em_comum,
                                      k_vizinhos, concordancia_minima)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING execucao_id
            """,
            (ANO_REFERENCIA, ANO_REFERENCIA, MINIMO_VOTACOES_EM_COMUM, K_VIZINHOS, CONCORDANCIA_MINIMA),
        )
        execucao_id = cursor.fetchone()[0]

        # O percentual nao entra no COPY: o banco calcula a partir dos contadores.
        copiar(cursor, 'COPY app.concordancia (deputado_a, deputado_b, votacoes_em_comum, concordancias, '
                       'execucao_id) FROM STDIN', pares.assign(execucao_id=execucao_id))
        copiar(cursor, 'COPY app.aresta (deputado_a, deputado_b, peso, execucao_id) FROM STDIN',
               arestas.assign(execucao_id=execucao_id))
        copiar(cursor, 'COPY app.posicao (deputado_id, x, y, execucao_id) FROM STDIN',
               posicoes.assign(execucao_id=execucao_id))
    return execucao_id


def main():
    if forcar_carga():
        print(f'FORCAR_CARGA ligado: {ANO_REFERENCIA} sera recarregado.')
    else:
        with conectar() as conexao:
            existente = carga_existente(conexao, ANO_REFERENCIA)
        if existente:
            execucao_id, posicoes = existente
            print(f'{ANO_REFERENCIA} ja carregado (execucao {execucao_id}, {posicoes} posicoes). '
                  'Pulando; use FORCAR_CARGA=1 para recarregar.')
            return

    pasta_brutos = baixar_dados_brutos()
    df_votos = ler_csv_camara(pasta_brutos / f'votacoesVotos-{ANO_REFERENCIA}.csv')
    ids = votacoes_de_merito(pasta_brutos)

    deputados = deputados_do_ano(df_votos)
    votacoes = votacoes_do_ano(pasta_brutos, ids)
    proposicoes, vinculos = proposicoes_das_votacoes(pasta_brutos, ids)
    votos = votos_das_votacoes(df_votos, ids)
    pares, arestas, posicoes = calcular_resultados(df_votos, ids, deputados)

    # Uma transacao so: se qualquer etapa falhar, o banco fica como estava.
    # A ordem respeita as chaves estrangeiras.
    with conectar() as conexao:
        total_deputados = carregar_deputados(conexao, deputados)
        total_proposicoes = carregar_proposicoes(conexao, proposicoes)
        total_votacoes, total_votos = carregar_votacoes(conexao, votacoes, vinculos, votos)
        partidos_corrigidos = atualizar_partido_atual(conexao)
        execucao_id = carregar_resultados(conexao, pares, arestas, posicoes)

    print(f'{ANO_REFERENCIA}: {total_deputados} deputados, {total_proposicoes} proposicoes, '
          f'{total_votacoes} votacoes de merito e {total_votos} votos gravados no banco.')
    print(f'{partidos_corrigidos} deputados com o partido atual recalculado pelos votos.')
    print(f'Execucao {execucao_id}: {len(pares)} pares com concordancia, {len(arestas)} arestas '
          f'e {len(posicoes)} posicoes gravados.')


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:  # qualquer falha vira uma linha clara no log e saida 1
        print(f'ERRO na carga de {ANO_REFERENCIA}: {type(erro).__name__}: {erro}', file=sys.stderr)
        print('Nada foi gravado no banco (a carga roda numa transacao so).', file=sys.stderr)
        if isinstance(erro, psycopg.errors.UndefinedTable):
            print('Falta tabela no banco: aplique o infra/db/init/01-schema.sql '
                  '(ou o CREATE TABLE app.posicao do README).', file=sys.stderr)
        elif isinstance(erro, psycopg.OperationalError):
            print('Sem conexao com o banco: confira a DATABASE_URL (ou as POSTGRES_* do .env).',
                  file=sys.stderr)
        sys.exit(1)
