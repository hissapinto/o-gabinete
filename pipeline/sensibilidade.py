"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/sensibilidade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Analise de sensibilidade pedida no parecer da parte 2: antes de afirmar
    que uma componente e o bloco politico "mais coeso", verificar quanto o
    resultado depende das escolhas de modelagem.

    O script refaz o grafo variando, um de cada vez:
        - K_VIZINHOS (k vizinhos mais parecidos);
        - CONCORDANCIA_MINIMA (limiar da aresta);
        - MINIMO_VOTACOES_EM_COMUM;
        - o desempate entre vizinhos de mesma concordancia (ordem dos
          vertices alfabetica, inversa e aleatoria);
    e, para cada grafo, mede componentes conexas, se a bancada do PSOL fica
    isolada e os blocos da opcao (j) do menu (arvore geradora maxima).

    Tambem calcula duas verificacoes da interpretacao politica:
        - coesao interna de cada partido (concordancia media entre os seus
          membros, sobre a matriz completa e nao so sobre as arestas);
        - participacao (votacoes registradas) dos deputados de maior grau.

    Nao altera dados/grafo.txt. Depende das etapas anteriores do pipeline
    (processamento.py e similaridade.py) ja terem sido executadas.

    Execucao, a partir da raiz do projeto:
        python pipeline/sensibilidade.py

Historico de alteracoes:
    19/11/2026 - Caio - Criacao.
"""

import os
import sys

import numpy as np
import pandas as pd

from utils import RAIZ
from coleta import ANO_REFERENCIA
from similaridade import matriz_de_votos, concordancia, MINIMO_VOTACOES_EM_COMUM
from gerar_grafo import (descartar_sem_par, montar_rotulos, chave_alfabetica,
                         escolher_arestas, K_VIZINHOS, CONCORDANCIA_MINIMA)

# Reaproveita a estrutura e os algoritmos da aplicacao de terminal.
sys.path.insert(0, os.path.join(RAIZ, "grafos", "negocio"))
from grafo import GrafoPonderadoND          # noqa: E402
from logica_grafos import componentes_conexas  # noqa: E402
import blocos                                # noqa: E402
import caracteristicas                       # noqa: E402

PARTIDO_ANALISADO = "PSOL"
SEMENTES_ALEATORIAS = (1, 2, 3, 4, 5)


# MONTAGEM DOS GRAFOS
def montar(C, rotulos, ordem, k, minimo):
    """Monta um GrafoPonderadoND com os vertices na ordem dada."""
    C_ord = C[np.ix_(ordem, ordem)]
    arestas = escolher_arestas(C_ord, k=k, minimo=minimo)
    g = GrafoPonderadoND(len(ordem))
    g.rotulos = [rotulos[i] for i in ordem]
    for (v, w), peso in arestas.items():
        g.insereA(v, w, peso)
    return g


def ordem_alfabetica(rotulos):
    return sorted(range(len(rotulos)), key=lambda i: chave_alfabetica(rotulos[i]))


def medir(g):
    """Medidas de um grafo para as tabelas de sensibilidade."""
    comps = sorted(componentes_conexas(g), key=len, reverse=True)
    partido = [blocos.partido_do_rotulo(g.rotulo(v)) for v in range(g.n)]
    do_partido = {v for v in range(g.n) if partido[v] == PARTIDO_ANALISADO}

    # componente que contem a bancada analisada: isolada se so tiver ela e
    # no maximo poucos de fora, e se nenhum membro estiver na componente gigante
    isolada = False
    for c in comps[1:]:
        if do_partido and do_partido <= set(c):
            isolada = True

    res = blocos.detectar_blocos(g, 3, 10)
    return {
        "vertices": g.n,
        "arestas": g.m,
        "componentes": len(comps),
        "tamanhos": [len(c) for c in comps[:4]],
        "psol_isolado": isolada,
        "blocos_3": [len(b) for b in res["blocos"]],
        "q_blocos": blocos.modularidade(g, res["blocos"]),
        "q_partidos": blocos.modularidade(g, blocos.blocos_por_partido(g)),
        "grau_max": max(g.grau(v) for v in range(g.n)),
    }


def linha(rotulo, m):
    return (f"| {rotulo} | {m['vertices']} | {m['arestas']} | {m['componentes']} "
            f"| {', '.join(map(str, m['tamanhos']))} | {'sim' if m['psol_isolado'] else 'nao'} "
            f"| {', '.join(map(str, m['blocos_3']))} | {m['q_blocos']:.3f} "
            f"| {m['q_partidos']:.3f} | {m['grau_max']} |")


CABECALHO = ("| Variacao | n | m | Comp. | Tamanhos | PSOL isolado | Blocos (k=3) "
             "| Q blocos | Q partidos | Grau max |\n|---|---|---|---|---|---|---|---|---|---|")


# EXECUCAO
def main():
    pasta = RAIZ / "dados" / "processado"
    votos = pd.read_csv(pasta / f"votos-{ANO_REFERENCIA}-merito.csv")
    deputados = pd.read_csv(pasta / "deputados.csv")
    matriz = matriz_de_votos(votos)

    def preparar(minimo_comum):
        df = concordancia(matriz, minimo_comum)
        ids, C, descartados = descartar_sem_par(df.index.to_numpy(), df.to_numpy(dtype=float))
        rotulos = montar_rotulos(ids, deputados)
        return ids, C, rotulos, descartados

    ids, C, rotulos, _ = preparar(MINIMO_VOTACOES_EM_COMUM)
    alfabetica = ordem_alfabetica(rotulos)
    base = montar(C, rotulos, alfabetica, K_VIZINHOS, CONCORDANCIA_MINIMA)

    print(f"# Analise de sensibilidade ({ANO_REFERENCIA})\n")
    print(f"Modelo base: k={K_VIZINHOS}, limiar={CONCORDANCIA_MINIMA}%, "
          f"minimo em comum={MINIMO_VOTACOES_EM_COMUM}, ordem alfabetica.\n")

    print("## 1. Numero de vizinhos (k)\n")
    print(CABECALHO)
    for k in (3, 4, 5, 6, 8, 10):
        print(linha(f"k={k}", medir(montar(C, rotulos, alfabetica, k, CONCORDANCIA_MINIMA))))

    print("\n## 2. Limiar de concordancia\n")
    print(CABECALHO)
    for limiar in (0, 70, 75, 80, 85, 90):
        print(linha(f"limiar={limiar}%", medir(montar(C, rotulos, alfabetica, K_VIZINHOS, limiar))))

    print("\n## 3. Minimo de votacoes em comum\n")
    print(CABECALHO)
    for minimo_comum in (10, 20, 30, 50, 70, 100):
        _i, C2, rot2, desc = preparar(minimo_comum)
        g = montar(C2, rot2, ordem_alfabetica(rot2), K_VIZINHOS, CONCORDANCIA_MINIMA)
        print(linha(f"minimo={minimo_comum} ({desc} fora)", medir(g)))

    print("\n## 4. Desempate entre vizinhos de mesma concordancia\n")
    print(CABECALHO)
    arestas_base = {(base.rotulo(v), base.rotulo(w)) for (v, w, _p) in base.arestas()}
    ordens = [("alfabetica", alfabetica), ("inversa", alfabetica[::-1])]
    for semente in SEMENTES_ALEATORIAS:
        ordens.append((f"aleatoria {semente}",
                       list(np.random.default_rng(semente).permutation(len(rotulos)))))
    for nome, ordem in ordens:
        g = montar(C, rotulos, ordem, K_VIZINHOS, CONCORDANCIA_MINIMA)
        pares = {tuple(sorted((g.rotulo(v), g.rotulo(w)))) for (v, w, _p) in g.arestas()}
        comuns = len(pares & {tuple(sorted(p)) for p in arestas_base})
        print(linha(f"{nome} ({comuns}/{len(arestas_base)} arestas iguais)", medir(g)))

    # coesao interna dos partidos sobre a matriz completa
    print("\n## 5. Coesao interna dos partidos (concordancia media entre membros)\n")
    print("| Partido | Deputados | Concordancia media interna | Desvio padrao |")
    print("|---|---|---|---|")
    partido = np.array([blocos.partido_do_rotulo(r) for r in rotulos])
    coesao = []
    for p in sorted(set(partido)):
        membros = np.where(partido == p)[0]
        if len(membros) < 5:
            continue
        sub = C[np.ix_(membros, membros)]
        valores = sub[np.triu_indices(len(membros), 1)]
        valores = valores[~np.isnan(valores)]
        coesao.append((p, len(membros), valores.mean(), valores.std()))
    for p, qtd, media, desvio in sorted(coesao, key=lambda x: -x[2]):
        print(f"| {p} | {qtd} | {media:.1f}% | {desvio:.1f} |")

    # participacao dos deputados de maior grau
    print("\n## 6. Participacao dos deputados de maior grau\n")
    participacao = (matriz != 0).sum(axis=1)
    por_id = dict(zip(matriz.index.to_numpy(), participacao.to_numpy()))
    ids_alfa = [int(ids[i]) for i in alfabetica]
    mediana = int(np.median([por_id[i] for i in ids_alfa]))
    print(f"Mediana de votacoes registradas por deputado: {mediana} de {matriz.shape[1]}.\n")
    print("| Deputado | Grau | Votacoes registradas |")
    print("|---|---|---|")
    resumo = caracteristicas.resumo_graus(base, quantos_maiores=10)
    for v, grau in resumo["maiores"]:
        print(f"| {base.rotulo(v)} | {grau} | {por_id[ids_alfa[v]]} |")

    graus = np.array([base.grau(v) for v in range(base.n)])
    part = np.array([por_id[i] for i in ids_alfa])
    correl = np.corrcoef(graus, part)[0, 1]
    print(f"\nCorrelacao entre grau e participacao: {correl:.2f}")


if __name__ == "__main__":
    main()
