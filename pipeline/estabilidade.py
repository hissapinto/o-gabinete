"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/estabilidade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Estabilidade dos blocos de votacao entre anos. Para cada ano refaz o
    grafo com o mesmo metodo do grafo.txt (k vizinhos, limiar e minimo de
    votacoes em comum), detecta os blocos com a arvore geradora maxima da
    opcao (j) do menu e mede:
        - tamanho dos blocos e modularidade, contra a dos partidos do ano;
        - alinhamento medio de cada bloco com a orientacao do Governo e da
          Oposicao (dado que nao entra no grafo);
        - quantos deputados ficam no mesmo bloco de um ano para o outro e
          o indice de Rand ajustado entre as duas divisoes.

    Os blocos de cada ano saem numerados por tamanho, e o numero nao
    significa nada de um ano para o outro. Para comparar anos, cada bloco
    recebe um nome pela regra de nomear_blocos: "Governo" e o bloco que
    mais vota com a orientacao do Governo; "Oposicao" e o maior dos blocos
    restantes que vota mais com a Oposicao do que com o Governo; os demais
    blocos de verdade sao "Terceiro", e os grupos avulsos, "Avulso".

    Usa o partido que o deputado tinha em cada ano (deputados-{ano}.csv),
    e nao o atual. Antes, cada ano precisa ter passado pelo processamento:
        ANO_REFERENCIA=2023 python pipeline/processamento.py   (e assim por diante)

    Execucao, a partir da raiz do projeto:
        python pipeline/estabilidade.py
        ANOS_ESTABILIDADE=2023,2024 python pipeline/estabilidade.py

    Grava dados/processado/estabilidade.json, lido por
    pipeline/figuras_estabilidade.py, e imprime as tabelas em Markdown.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

import collections
import json
import os
import sys

import pandas as pd

from utils import RAIZ
from coleta import baixar
from similaridade import matriz_de_votos, concordancia
from gerar_grafo import descartar_sem_par, montar_rotulos, montar_grafo
import alinhamento_governo as ag

# Reaproveita a estrutura e os algoritmos da aplicacao de terminal.
sys.path.insert(0, os.path.join(RAIZ, "grafos", "negocio"))
from grafo import GrafoPonderadoND  # noqa: E402
import blocos  # noqa: E402

ANOS = [int(a) for a in os.environ.get("ANOS_ESTABILIDADE", "2023,2024,2025,2026").split(",")]
NUM_BLOCOS = 3
TAMANHO_MINIMO = 10
URL_ORIENTACOES = ("https://dadosabertos.camara.leg.br/arquivos/votacoesOrientacoes/csv/"
                   "votacoesOrientacoes-{ano}.csv")


# GRAFO E BLOCOS DE UM ANO
def grafo_do_ano(votos, deputados):
    """
    Refaz o grafo do ano como o gerar_grafo.py faz o grafo.txt.
    Devolve (ids na ordem dos vertices, GrafoPonderadoND, quantos deputados
    ficaram fora por nao terem par valido).
    """
    C = concordancia(matriz_de_votos(votos))
    ids, Cm, fora = descartar_sem_par(C.index.to_numpy(), C.to_numpy(dtype=float))
    rotulos = montar_rotulos(ids, deputados)
    ids, rotulos, arestas = montar_grafo(ids, Cm, rotulos)
    g = GrafoPonderadoND(len(ids))
    g.rotulos = list(rotulos)
    for (v, w), peso in arestas.items():
        g.insereA(v, w, peso)
    return ids, g, fora


def nomear_blocos(grupos, significativos, alin_gov, alin_opo):
    """
    Nome de cada grupo devolvido por blocos.detectar_blocos.

    grupos         lista de listas de deputado_id, do maior ao menor;
    significativos quantos grupos contam como bloco;
    alin_gov/opo   {deputado_id: % de votos iguais a orientacao}, so com
                   quem tem alinhamento calculado.

    Regra (documentada na sintese): o bloco de maior alinhamento medio com o
    Governo e "Governo"; entre os outros blocos que votam mais com a Oposicao
    do que com o Governo, o maior e "Oposicao"; os demais blocos sao
    "Terceiro"; grupos alem dos significativos sao "Avulso".
    """
    def media(grupo, alin):
        valores = [alin[i] for i in grupo if i in alin]
        return sum(valores) / len(valores) if valores else -1.0

    blocos_reais = range(min(significativos, len(grupos)))
    nomes = ["Avulso"] * len(grupos)
    if not blocos_reais:
        return nomes
    gov = max(blocos_reais, key=lambda b: media(grupos[b], alin_gov))
    nomes[gov] = "Governo"
    candidatos = [b for b in blocos_reais if b != gov
                  and media(grupos[b], alin_opo) > media(grupos[b], alin_gov)]
    if candidatos:
        nomes[max(candidatos, key=lambda b: (len(grupos[b]), -b))] = "Oposição"
    for b in blocos_reais:
        if nomes[b] == "Avulso":
            nomes[b] = "Terceiro"
    return nomes


# COMPARACAO ENTRE ANOS
def transicoes(antes, depois):
    """
    antes/depois: {deputado_id: nome do bloco}. Conta, so para os deputados
    presentes nos dois anos, quantos foram de cada bloco para cada bloco.
    """
    return collections.Counter((antes[i], depois[i]) for i in antes if i in depois)


def indice_rand_ajustado(x, y):
    """
    Indice de Rand ajustado (Hubert e Arabie, 1985) entre duas divisoes dos
    mesmos elementos, dadas como listas de rotulos na mesma ordem. Vale 1
    quando as divisoes sao iguais e fica perto de 0 quando a concordancia e a
    esperada ao acaso. Nao depende do nome dado aos grupos.
    """
    if len(x) != len(y):
        raise ValueError("as duas divisoes precisam ter os mesmos elementos")
    n = len(x)
    if n < 2:
        return 1.0

    def pares(k):
        return k * (k - 1) / 2

    soma = sum(pares(v) for v in collections.Counter(zip(x, y)).values())
    soma_x = sum(pares(v) for v in collections.Counter(x).values())
    soma_y = sum(pares(v) for v in collections.Counter(y).values())
    esperado = soma_x * soma_y / pares(n)
    maximo = (soma_x + soma_y) / 2
    if maximo == esperado:
        return 1.0
    return (soma - esperado) / (maximo - esperado)


# ANALISE DE UM ANO
def analisar_ano(ano):
    processado = RAIZ / "dados" / "processado"
    brutos = RAIZ / "dados" / "brutos"
    arq_votos = processado / f"votos-{ano}-merito.csv"
    arq_deps = processado / f"deputados-{ano}.csv"
    if not arq_votos.exists() or not arq_deps.exists():
        raise FileNotFoundError(
            f"faltam os dados de {ano}: rode ANO_REFERENCIA={ano} python pipeline/processamento.py")

    votos = pd.read_csv(arq_votos)
    deputados = pd.read_csv(arq_deps)
    arq_or = brutos / f"votacoesOrientacoes-{ano}.csv"
    url = URL_ORIENTACOES.format(ano=ano)
    baixar(url, arq_or)
    df_or = pd.read_csv(arq_or, sep=";", encoding="utf-8-sig")

    ids, g, fora = grafo_do_ano(votos, deputados)
    res = blocos.detectar_blocos(g, NUM_BLOCOS, TAMANHO_MINIMO)
    grupos = [[int(ids[v]) for v in grupo] for grupo in res["blocos"]]

    merito = set(votos["idVotacao"])
    alin, orientadas = {}, {}
    for bancada in ag.BANCADAS:
        o = ag.orientacoes(df_or, bancada)
        o = o[o.index.isin(merito)]
        a = ag.alinhamento(votos, o).set_index("deputado_id")["alinhamento"].dropna()
        alin[bancada] = {int(i): float(v) for i, v in a.items()}
        orientadas[bancada] = int(len(o))

    nomes = nomear_blocos(grupos, res["significativos"], alin["Governo"], alin["Oposição"])
    partido = deputados.set_index("deputado_id")["deputado_siglaPartido"].to_dict()
    nome = deputados.set_index("deputado_id")["deputado_nome"].to_dict()

    deps = {}
    for grupo, bloco in zip(grupos, nomes):
        for i in grupo:
            deps[str(i)] = {"nome": nome[i], "partido": partido[i], "bloco": bloco,
                            "gov": alin["Governo"].get(i), "opo": alin["Oposição"].get(i)}

    return {
        "ano": ano,
        "votacoes_merito": len(merito),
        "fora_do_grafo": int(fora),
        "vertices": g.n,
        "arestas": g.m,
        "blocos": [{"nome": b, "tamanho": len(grupo)} for grupo, b in zip(grupos, nomes)],
        "modularidade_blocos": blocos.modularidade(g, res["blocos"]),
        "modularidade_partidos": blocos.modularidade(g, blocos.blocos_por_partido(g)),
        "orientadas": orientadas,
        "deputados": deps,
        "lista_arestas": [[int(ids[v]), int(ids[w]), p] for (v, w, p) in g.arestas()],
    }


def media(valores):
    valores = [v for v in valores if v is not None]
    return sum(valores) / len(valores) if valores else float("nan")


def imprimir(resultado):
    print("| Ano | Votações de mérito | No grafo (fora) | Governo / Oposição / 3º | "
          "Q blocos | Q partidos | Bloco Gov. com o Governo | Bloco Opo. com a Oposição |")
    print("|---|---|---|---|---|---|---|---|")
    for r in resultado["anos"]:
        tam = collections.Counter()
        for b in r["blocos"]:
            tam[b["nome"]] += b["tamanho"]
        deps = r["deputados"].values()
        gov = media(d["gov"] for d in deps if d["bloco"] == "Governo")
        opo = media(d["opo"] for d in deps if d["bloco"] == "Oposição")
        print(f"| {r['ano']} | {r['votacoes_merito']} | {r['vertices']} ({r['fora_do_grafo']}) | "
              f"{tam['Governo']} / {tam['Oposição']} / {tam['Terceiro']} | "
              f"{r['modularidade_blocos']:.3f} | {r['modularidade_partidos']:.3f} | {gov:.1f}% | {opo:.1f}% |")

    print("\n| Passagem | Nos dois anos | No mesmo bloco | Entre Governo e Oposição | Rand ajustado |")
    print("|---|---|---|---|---|")
    for p in resultado["passagens"]:
        print(f"| {p['de']} → {p['para']} | {p['em_comum']} | {100 * p['mesmo_bloco'] / p['em_comum']:.1f}% | "
              f"{p['gov_opo_trocaram']} | {p['rand_ajustado']:.2f} |")


def main():
    # o terminal do Windows nao e UTF-8 por padrao (acentos e setas das tabelas)
    sys.stdout.reconfigure(encoding="utf-8")
    anos = [analisar_ano(ano) for ano in ANOS]
    passagens = []
    for r1, r2 in zip(anos, anos[1:]):
        antes = {i: d["bloco"] for i, d in r1["deputados"].items()}
        depois = {i: d["bloco"] for i, d in r2["deputados"].items()}
        comuns = [i for i in antes if i in depois]
        tab = transicoes(antes, depois)
        lados = ("Governo", "Oposição")
        passagens.append({
            "de": r1["ano"], "para": r2["ano"], "em_comum": len(comuns),
            "mesmo_bloco": sum(v for (a, b), v in tab.items() if a == b),
            "gov_opo_trocaram": sum(v for (a, b), v in tab.items() if a != b and a in lados and b in lados),
            "rand_ajustado": indice_rand_ajustado([antes[i] for i in comuns], [depois[i] for i in comuns]),
            "fluxos": [[a, b, v] for (a, b), v in sorted(tab.items())],
        })

    resultado = {"anos": anos, "passagens": passagens}
    saida = RAIZ / "dados" / "processado" / "estabilidade.json"
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False)
    imprimir(resultado)
    print(f"\nResultado gravado em {saida}")


if __name__ == "__main__":
    main()
