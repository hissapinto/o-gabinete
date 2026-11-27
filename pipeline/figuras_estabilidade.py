"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/figuras_estabilidade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Figuras da analise de estabilidade dos blocos entre anos, a partir de
    dados/processado/estabilidade.json (gravado por pipeline/estabilidade.py):
        - fig_fluxo_blocos.png: deputados que ficam ou mudam de bloco de um
          ano para o outro, com o que aconteceu em cada passagem;
        - fig_partidos_no_governo.png: porcentagem de cada partido no bloco
          do Governo, com o partido do proprio ano;
        - fig_alinhamento_anos.png: alinhamento de cada deputado com a
          orientacao do Governo, por bloco e ano;
        - fig_grafos_por_ano.png: o grafo de cada ano colorido pelo bloco,
          com o layout do pipeline/layout.py.

    Fica fora da carga e do CI: depende do matplotlib, que esta no
    requirements-notebook.txt e nao no requirements.txt.

    Execucao, a partir da raiz do projeto:
        python pipeline/figuras_estabilidade.py [pasta de saida]
    A pasta padrao e dados/processado/figuras/ (fora do git).

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

import collections
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

from utils import RAIZ  # noqa: E402
from layout import calcular_layout  # noqa: E402

AZUL, LARANJA, VERDE, VERDE_TXT = "#2a78d6", "#eb6834", "#1baf7a", "#0f7a55"
TXT, TXT2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
COR = {"Governo": AZUL, "Oposição": LARANJA, "Terceiro": VERDE}
ORDEM = ["Governo", "Terceiro", "Oposição"]
NOMES = {"Governo": "Bloco do Governo", "Terceiro": "3º bloco", "Oposição": "Bloco da Oposição"}
PARTIDOS_DESTAQUE = {"MDB": "#8c6d31", "REPUBLICANOS": "#5a7d2a", "PSD": "#2f9e8f", "UNIÃO": "#d9467a",
                     "PP": "#7a5195", "PODE": "#e0a100", "PL": LARANJA}
NOME_PARTIDO = {"REPUBLICANOS": "Republicanos", "UNIÃO": "União", "PODE": "Podemos"}

plt.rcParams.update({
    "font.family": "Arial", "font.size": 9, "axes.edgecolor": GRADE, "axes.labelcolor": TXT2,
    "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.dpi": 300,
})


def salvar(fig, pasta, nome):
    fig.tight_layout()
    fig.savefig(pasta / nome, bbox_inches="tight")
    plt.close(fig)


def no_bloco(ano, bloco, campo=None):
    deps = [d for d in ano["deputados"].values() if d["bloco"] == bloco]
    return deps if campo is None else [d[campo] for d in deps if d[campo] is not None]


def rotulo_terceiro(ano):
    """'PSOL' ou os dois partidos mais frequentes do 3o bloco ('PL + NOVO')."""
    cont = collections.Counter(d["partido"] for d in no_bloco(ano, "Terceiro"))
    if not cont:
        return ""
    if cont.most_common(1)[0][0] == "PSOL":
        return "PSOL"
    return " + ".join(p for p, _ in cont.most_common(2))


def resumo_passagem(antes, depois):
    """Frase sobre a maior mudanca de bloco entre dois anos, com os partidos de quem mudou."""
    mudaram = collections.defaultdict(list)
    for i, d in antes["deputados"].items():
        novo = depois["deputados"].get(i)
        if novo and d["bloco"] != novo["bloco"] and d["bloco"] in COR and novo["bloco"] in COR:
            mudaram[(d["bloco"], novo["bloco"])].append(novo["partido"])
    if not mudaram:
        return "ninguém mudou de bloco"
    (a, b), partidos = max(mudaram.items(), key=lambda par: len(par[1]))
    principais = ", ".join(NOME_PARTIDO.get(p, p) for p, _ in collections.Counter(partidos).most_common(3))
    curto = {"Governo": "Governo", "Oposição": "Oposição", "Terceiro": "3º bloco"}
    return f"{len(partidos)} deputados: {curto[a]} → {curto[b]}\n(mais de {principais})"


def fig_fluxo(r, pasta):
    anos = r["anos"]
    fig, ax = plt.subplots(figsize=(7.4, 4.9))
    ax.grid(False)
    ax.axis("off")
    larg, esp = 0.13, 26
    pos = {}
    for k, ano in enumerate(anos):
        tam = collections.Counter()
        for b in ano["blocos"]:
            tam[b["nome"]] += b["tamanho"]
        y = 0
        for bloco in ORDEM:
            pos[(k, bloco)] = [y, y]  # cursor de saida, cursor de entrada
            if tam[bloco]:
                ax.add_patch(plt.Rectangle((k - larg / 2, y), larg, tam[bloco], color=COR[bloco], lw=0, zorder=3))
                ax.text(k, y + tam[bloco] / 2, str(tam[bloco]), ha="center", va="center", color="white",
                        fontsize=8, fontweight="bold", zorder=4)
            if bloco == "Terceiro" and tam[bloco]:
                ax.text(k, y + tam[bloco] + 3, rotulo_terceiro(ano), ha="center", va="top", color=VERDE_TXT,
                        fontsize=7, fontweight="bold", zorder=4)
            y += tam[bloco] + esp
            if k == 0:
                ax.text(-larg / 2 - 0.05, pos[(k, bloco)][0] + tam[bloco] / 2,
                        NOMES[bloco].replace(" da ", " da\n").replace(" do ", " do\n"), ha="right", va="center",
                        color=VERDE_TXT if bloco == "Terceiro" else COR[bloco], fontsize=8.5, fontweight="bold")
        ax.text(k, -40, str(ano["ano"]), ha="center", va="center", color=TXT, fontsize=10, fontweight="bold")

    for k, p in enumerate(r["passagens"]):
        ax.text(k + 0.5, -40, f"{100 * p['mesmo_bloco'] / p['em_comum']:.0f}% ficaram\nno mesmo bloco",
                ha="center", va="center", color=TXT2, fontsize=7.5)
        fluxos = {(a, b): v for a, b, v in p["fluxos"]}
        for a in ORDEM:
            for b in ORDEM:
                v = fluxos.get((a, b), 0)
                if not v:
                    continue
                y0, y1 = pos[(k, a)][0], pos[(k + 1, b)][1]
                pos[(k, a)][0] += v
                pos[(k + 1, b)][1] += v
                x0, x1 = k + larg / 2, k + 1 - larg / 2
                xm = (x0 + x1) / 2
                verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 + v), (xm, y1 + v), (xm, y0 + v),
                         (x0, y0 + v), (x0, y0)]
                codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO,
                         MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
                mudou = a != b
                ax.add_patch(PathPatch(MPath(verts, codes), facecolor=COR[a], alpha=0.75 if mudou else 0.16,
                                       lw=0, zorder=2 if mudou else 1))
                if mudou and v >= 10:
                    ax.text(x0 + 0.2, y0 + v / 2 + v * 0.25 * (1 if y1 > y0 else -1), str(v), ha="center",
                            va="center", fontsize=7.5, fontweight="bold", color=COR[a], zorder=5,
                            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=COR[a], lw=0.6))
        ax.text(k + 0.5, 625, resumo_passagem(anos[k], anos[k + 1]),
                ha="center", va="top", fontsize=7.2, color=TXT, linespacing=1.35)
    ax.text((len(anos) - 1) / 2, 730,
            "Números nas barras: deputados no bloco naquele ano.  Faixa clara: ficou no mesmo bloco.  "
            "Faixa forte: mudou de bloco (número = deputados).\n"
            "Só entram nas faixas os deputados que estão no grafo dos dois anos.",
            ha="center", va="top", fontsize=6.8, color=TXT2)
    ax.set_xlim(-0.55, len(anos) - 0.65)
    ax.set_ylim(-60, 790)
    ax.invert_yaxis()
    salvar(fig, pasta, "fig_fluxo_blocos.png")


def fig_partidos(r, pasta):
    anos = [a["ano"] for a in r["anos"]]
    pct = {}
    for ano in r["anos"]:
        for partido in PARTIDOS_DESTAQUE:
            deps = [d for d in ano["deputados"].values() if d["partido"] == partido]
            pct[(partido, ano["ano"])] = (100 * sum(d["bloco"] == "Governo" for d in deps) / len(deps)
                                          if deps else np.nan)
    fig, ax = plt.subplots(figsize=(6.3, 3.1))
    ultimo = -99
    for v, partido in sorted((pct[(p, anos[-1])], p) for p in PARTIDOS_DESTAQUE):
        y = max(v, ultimo + 4.2)  # rotulos sem sobrepor
        ultimo = y
        ax.text(anos[-1] + 0.1, y, NOME_PARTIDO.get(partido, partido), va="center", fontsize=7.5,
                color=PARTIDOS_DESTAQUE[partido])
    for partido, cor in PARTIDOS_DESTAQUE.items():
        ax.plot(anos, [pct[(partido, a)] for a in anos], marker="o", ms=3.5, color=cor, lw=1.6)
    ax.set_xticks(anos)
    ax.set_xlim(anos[0] - 0.2, anos[-1] + 0.7)
    ax.set_ylim(0, 102)
    ax.set_ylabel("% dos deputados do partido\nno bloco do Governo")
    ax.grid(axis="x", visible=False)
    salvar(fig, pasta, "fig_partidos_no_governo.png")


def fig_alinhamento(r, pasta):
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    rng = np.random.default_rng(7)
    for k, ano in enumerate(r["anos"]):
        for j, bloco in enumerate(["Governo", "Terceiro", "Oposição"]):
            v = np.array(no_bloco(ano, bloco, "gov"))
            if not len(v):
                continue
            xc = k + (j - 1) * 0.26
            ax.scatter(xc + rng.uniform(-0.09, 0.09, len(v)), v, s=4, color=COR[bloco], alpha=0.45, lw=0)
            ax.hlines(np.median(v), xc - 0.11, xc + 0.11, color=TXT, lw=1.4)
    ax.set_xticks(range(len(r["anos"])), [str(a["ano"]) for a in r["anos"]])
    ax.set_ylim(0, 102)
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("% dos votos iguais à\norientação do Governo")
    ax.grid(axis="x", visible=False)
    ax.legend([Line2D([], [], marker="o", ls="", color=COR[b], ms=5) for b in ["Governo", "Terceiro", "Oposição"]],
              [NOMES[b] for b in ["Governo", "Terceiro", "Oposição"]], loc="lower left", fontsize=7.5,
              frameon=False, ncol=3)
    salvar(fig, pasta, "fig_alinhamento_anos.png")


def fig_grafos(r, pasta):
    fig, eixos = plt.subplots(1, len(r["anos"]), figsize=(1.8 * len(r["anos"]), 2.2))
    for ax, ano in zip(np.atleast_1d(eixos), r["anos"]):
        ids = [int(i) for i in ano["deputados"]]
        partidos = {int(i): d["partido"] for i, d in ano["deputados"].items()}
        arestas = {(a, b): p for a, b, p in ano["lista_arestas"]}
        xy = calcular_layout(ids, partidos, arestas)
        segs = [((xy[a][0], -xy[a][1]), (xy[b][0], -xy[b][1])) for a, b in arestas]
        ax.add_collection(LineCollection(segs, colors="#dcdbd7", linewidths=0.2, zorder=1))
        cores = [COR.get(ano["deputados"][str(i)]["bloco"], "#b9b8b3") for i in ids]
        ax.scatter([xy[i][0] for i in ids], [-xy[i][1] for i in ids], s=2.2, c=cores, lw=0, zorder=2)
        ax.set_title(str(ano["ano"]), fontsize=9, color=TXT)
        ax.axis("off")
        ax.set_aspect("equal")
        ax.autoscale()
    fig.legend([Line2D([], [], marker="o", ls="", color=COR[b], ms=5) for b in ORDEM], [NOMES[b] for b in ORDEM],
               loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.04))
    salvar(fig, pasta, "fig_grafos_por_ano.png")


def main():
    with open(RAIZ / "dados" / "processado" / "estabilidade.json", encoding="utf-8") as f:
        r = json.load(f)
    pasta = RAIZ / "dados" / "processado" / "figuras" if len(sys.argv) < 2 else RAIZ / sys.argv[1]
    pasta.mkdir(parents=True, exist_ok=True)
    fig_fluxo(r, pasta)
    fig_partidos(r, pasta)
    fig_alinhamento(r, pasta)
    fig_grafos(r, pasta)
    print(f"Figuras gravadas em {pasta}")


if __name__ == "__main__":
    main()
