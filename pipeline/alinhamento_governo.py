"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/alinhamento_governo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Validacao externa dos blocos encontrados pela opcao (j) do menu. O parecer
    da parte 2 pediu que a interpretacao politica dos resultados fosse
    validada; aqui ela e confrontada com um dado que NAO entrou no grafo: a
    orientacao oficial das liderancas do Governo e da Oposicao em cada
    votacao (arquivo votacoesOrientacoes da Camara).

    Para cada deputado, calcula o alinhamento com a orientacao de uma
    bancada: entre as votacoes de merito em que a bancada orientou Sim ou
    Nao (ou Obstrucao, que conta como Nao) e o deputado votou, a fracao em
    que o voto coincidiu com a orientacao. Orientacao "Liberado" fica fora.

    Depois resume o alinhamento por bloco e por partido.

    Execucao, a partir da raiz do projeto (depois de processamento.py e
    similaridade.py):
        python pipeline/alinhamento_governo.py

Historico de alteracoes:
    20/11/2026 - Kaique - Criacao.
"""

import os
import sys

import numpy as np
import pandas as pd

from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar
from similaridade import VALOR_VOTO, MINIMO_VOTACOES_EM_COMUM, concordancia, matriz_de_votos
from gerar_grafo import descartar_sem_par, montar_rotulos, chave_alfabetica

sys.path.insert(0, os.path.join(RAIZ, "grafos", "negocio"))
sys.path.insert(0, os.path.join(RAIZ, "grafos", "persistencia"))
import blocos            # noqa: E402
import persistencia      # noqa: E402

URL_ORIENTACOES = ('https://dadosabertos.camara.leg.br/arquivos/votacoesOrientacoes/csv/'
                   f'votacoesOrientacoes-{ANO_REFERENCIA}.csv')
VALOR_ORIENTACAO = {'Sim': 1, 'Não': -1, 'Obstrução': -1}   # Liberado fica de fora
BANCADAS = ('Governo', 'Oposição')
MINIMO_VOTACOES_ORIENTADAS = 10


def orientacoes(df_orient, bancada):
    """Serie idVotacao -> +1/-1 com a orientacao da bancada (sem 'Liberado')."""
    sel = df_orient[df_orient['siglaBancada'] == bancada].copy()
    sel['valor'] = sel['orientacao'].map(VALOR_ORIENTACAO)
    sel = sel.dropna(subset=['valor']).drop_duplicates('idVotacao', keep='last')
    return sel.set_index('idVotacao')['valor'].astype(int)


def alinhamento(df_votos, orient, minimo=MINIMO_VOTACOES_ORIENTADAS):
    """
    Percentual (0 a 100) de votos de cada deputado iguais a orientacao, so
    nas votacoes orientadas em que ele votou Sim, Nao ou Obstrucao.
    Deputados com menos de 'minimo' votacoes nessa condicao ficam NaN.
    Devolve um DataFrame com deputado_id, alinhamento e votacoes.
    """
    v = df_votos.assign(valor=df_votos['voto'].map(VALOR_VOTO))
    v = v.dropna(subset=['valor'])
    v = v[v['idVotacao'].isin(orient.index)]
    v = v.assign(igual=(v['valor'].astype(int) == v['idVotacao'].map(orient)).astype(int))
    g = v.groupby('deputado_id')['igual'].agg(['mean', 'size'])
    g.columns = ['alinhamento', 'votacoes']
    g['alinhamento'] = (g['alinhamento'] * 100).where(g['votacoes'] >= minimo)
    return g.reset_index()


def ids_na_ordem_do_grafo(votos, deputados):
    """
    Refaz a ordem dos vertices do grafo.txt (deputados com par valido, em
    ordem alfabetica) e devolve os ids dos deputados nessa ordem e os rotulos.
    """
    df = concordancia(matriz_de_votos(votos), MINIMO_VOTACOES_EM_COMUM)
    ids, _C, _d = descartar_sem_par(df.index.to_numpy(), df.to_numpy(dtype=float))
    rotulos = montar_rotulos(ids, deputados)
    ordem = sorted(range(len(rotulos)), key=lambda i: chave_alfabetica(rotulos[i]))
    return [int(ids[i]) for i in ordem], [rotulos[i] for i in ordem]


def resumo_por_grupo(alin, grupos, nomes):
    """Media, mediana e quantidade de deputados com valor, por grupo."""
    linhas = []
    for nome, membros in zip(nomes, grupos):
        x = alin.reindex(membros).dropna()
        linhas.append((nome, len(membros), x.mean(), x.median(), x.quantile(0.1), x.quantile(0.9)))
    return linhas


def main():
    brutos = RAIZ / 'dados' / 'brutos'
    pasta = RAIZ / 'dados' / 'processado'
    arq = brutos / URL_ORIENTACOES.split('/')[-1]
    baixar(URL_ORIENTACOES, arq)

    df_orient = pd.read_csv(arq, sep=';', encoding='utf-8-sig')
    votos = pd.read_csv(pasta / f'votos-{ANO_REFERENCIA}-merito.csv')
    deputados = pd.read_csv(pasta / 'deputados.csv')
    merito = set(votos['idVotacao'])

    ids, rotulos = ids_na_ordem_do_grafo(votos, deputados)
    grafo = persistencia.ler(str(RAIZ / 'dados' / 'grafo.txt'))
    # A Camara as vezes atualiza o nome parlamentar nos arquivos (ex.: um
    # deputado que mudou de nome depois da geracao do grafo.txt). Algumas
    # trocas isoladas sao aceitas; uma diferenca maior indica ordem errada.
    diferentes = [(v, a, b) for v, (a, b) in enumerate(zip(grafo.rotulos, rotulos)) if a != b]
    if grafo.n != len(rotulos) or len(diferentes) > 3:
        raise RuntimeError('a ordem refeita nao bate com dados/grafo.txt')
    for (v, a, b) in diferentes:
        print(f'Aviso: vertice {v} chama-se "{a}" no grafo.txt e "{b}" nos dados atuais.')

    res = blocos.detectar_blocos(grafo, 3, 10)
    grupos_ids = [[ids[v] for v in b] for b in res['blocos']]
    nomes = [f'Bloco {k + 1} ({len(b)})' for k, b in enumerate(res['blocos'])]

    print(f'# Alinhamento com as orientacoes de bancada ({ANO_REFERENCIA})\n')
    for bancada in BANCADAS:
        o = orientacoes(df_orient, bancada)
        o = o[o.index.isin(merito)]
        alin = alinhamento(votos, o).set_index('deputado_id')['alinhamento']
        print(f'## {bancada}: {len(o)} das {len(merito)} votacoes de merito orientadas\n')
        print('| Grupo | Deputados | Media | Mediana | 10% | 90% |\n|---|---|---|---|---|---|')
        for (nome, n, media, med, p10, p90) in resumo_por_grupo(alin, grupos_ids, nomes):
            print(f'| {nome} | {n} | {media:.1f}% | {med:.1f}% | {p10:.1f}% | {p90:.1f}% |')

        partido = {i: blocos.partido_do_rotulo(r) for i, r in zip(ids, rotulos)}
        por_partido = {}
        for i in ids:
            por_partido.setdefault(partido[i], []).append(i)
        grandes = sorted((p for p in por_partido if len(por_partido[p]) >= 7),
                         key=lambda p: -alin.reindex(por_partido[p]).mean())
        print('\n| Partido | Deputados | Media |\n|---|---|---|')
        for p in grandes:
            print(f'| {p} | {len(por_partido[p])} | {alin.reindex(por_partido[p]).mean():.1f}% |')
        print()

    # deputados do bloco 1 que mais se afastam do governo, e do bloco 2 que mais se aproximam
    o = orientacoes(df_orient, 'Governo')
    alin = alinhamento(votos, o[o.index.isin(merito)]).set_index('deputado_id')['alinhamento']
    nome = dict(zip(ids, rotulos))
    for k, ordem in ((0, True), (1, False)):
        x = alin.reindex(grupos_ids[k]).dropna().sort_values(ascending=ordem).head(5)
        print(f'Extremos do bloco {k + 1}:', '; '.join(f'{nome[i]} {v:.0f}%' for i, v in x.items()))


if __name__ == '__main__':
    main()
