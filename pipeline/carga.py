import os

import pandas as pd
import psycopg

from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar_dados_brutos
from processamento import ler_csv_camara, votacoes_de_merito


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
    config = ler_configuracao()
    return psycopg.connect(
        host=config.get('POSTGRES_HOST', 'localhost'),
        port=config.get('POSTGRES_PORT', '5432'),
        dbname=config['POSTGRES_DB'],
        user=config['POSTGRES_USER'],
        password=config.get('POSTGRES_PASSWORD', ''),
    )


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


if __name__ == "__main__":
    pasta_brutos = baixar_dados_brutos()
    df_votos = ler_csv_camara(pasta_brutos / f'votacoesVotos-{ANO_REFERENCIA}.csv')
    ids = votacoes_de_merito(pasta_brutos)

    deputados = deputados_do_ano(df_votos)
    votacoes = votacoes_do_ano(pasta_brutos, ids)
    proposicoes, vinculos = proposicoes_das_votacoes(pasta_brutos, ids)
    votos = votos_das_votacoes(df_votos, ids)

    # Uma transacao so: se qualquer etapa falhar, o banco fica como estava.
    # A ordem respeita as chaves estrangeiras.
    with conectar() as conexao:
        total_deputados = carregar_deputados(conexao, deputados)
        total_proposicoes = carregar_proposicoes(conexao, proposicoes)
        total_votacoes, total_votos = carregar_votacoes(conexao, votacoes, vinculos, votos)
        partidos_corrigidos = atualizar_partido_atual(conexao)

    print(f'{ANO_REFERENCIA}: {total_deputados} deputados, {total_proposicoes} proposicoes, '
          f'{total_votacoes} votacoes de merito e {total_votos} votos gravados no banco.')
    print(f'{partidos_corrigidos} deputados com o partido atual recalculado pelos votos.')
