
import unicodedata
import numpy as np
import pandas as pd
from utils import RAIZ
from coleta import ANO_REFERENCIA

TIPO_GRAFO = 2
K_VIZINHOS = 5
CONCORDANCIA_MINIMA = 75  # em %, a confirmar com o professor


def carregar_concordancia(pasta):
    """Le a matriz e descarta deputados sem nenhum par valido."""
    df = pd.read_csv(pasta / f'similaridade-{ANO_REFERENCIA}.csv', index_col=0)
    ids = df.index.to_numpy()
    C = df.to_numpy(dtype=float)
    np.fill_diagonal(C, np.nan)

    com_par = ~np.isnan(C).all(axis=1)
    return ids[com_par], C[np.ix_(com_par, com_par)], int((~com_par).sum())


def montar_rotulos(ids, pasta):
    """Rotulo do vertice no formato 'Nome (PARTIDO-UF)'."""
    dep = pd.read_csv(pasta / 'deputados.csv').set_index('deputado_id')
    rotulos = []
    for i in ids:
        nome = str(dep.at[i, 'deputado_nome']).replace('"', "'")
        rotulos.append(f"{nome} ({dep.at[i, 'deputado_siglaPartido']}-{dep.at[i, 'deputado_siglaUf']})")
    return rotulos


def chave_alfabetica(texto):
    """Chave de ordenacao que ignora acentos e maiusculas ('Átila' junto de 'Atila')."""
    sem_acento = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return sem_acento.casefold()


def escolher_arestas(C, k=K_VIZINHOS, minimo=CONCORDANCIA_MINIMA):
    """Devolve {(v, w): peso} com v < w, ligando cada vertice aos k mais parecidos."""
    C0 = np.nan_to_num(C, nan=-1.0)
    arestas = {}
    for v in range(len(C0)):
        for w in np.argsort(-C0[v])[:k]:
            w = int(w)
            if C0[v, w] >= minimo:
                arestas[(min(v, w), max(v, w))] = int(round(C0[v, w]))
    return arestas


def gravar_grafo(caminho, rotulos, arestas):
    """Grava no mesmo formato lido pela opcao (a) do menu."""
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        arquivo.write(f'{TIPO_GRAFO}\n{len(rotulos)}\n')
        for v, rotulo in enumerate(rotulos):
            arquivo.write(f'{v} "{rotulo}"\n')
        arquivo.write(f'{len(arestas)}\n')
        for (v, w), peso in sorted(arestas.items()):
            arquivo.write(f'{v} {w} {peso}\n')


if __name__ == "__main__":
    pasta = RAIZ / 'dados' / 'processado'
    ids, C, descartados = carregar_concordancia(pasta)
    rotulos = montar_rotulos(ids, pasta)

    # vertices em ordem alfabetica, para facilitar a leitura do arquivo
    ordem = sorted(range(len(rotulos)), key=lambda i: chave_alfabetica(rotulos[i]))
    C = C[np.ix_(ordem, ordem)]
    rotulos = [rotulos[i] for i in ordem]

    arestas = escolher_arestas(C)
    grau = np.zeros(len(rotulos), dtype=int)
    for v, w in arestas:
        grau[v] += 1
        grau[w] += 1

    caminho = RAIZ / 'dados' / 'grafo.txt'
    gravar_grafo(caminho, rotulos, arestas)

    print(f'{len(rotulos)} vertices ({descartados} deputados descartados sem par valido)')
    print(f'{len(arestas)} arestas | vertices isolados: {(grau == 0).sum()}')
    print(f'Grafo salvo em {caminho}')