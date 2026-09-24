"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/negocio/grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Estrutura de dados do grafo. Implementa um grafo NAO ORIENTADO COM PESO
    NA ARESTA (tipo 2), como lista de adjacencia, estendendo a classe Grafo
    apresentada em aula (grafoLista.py).

    Cada posicao da lista de adjacencia guarda tuplas (vizinho, peso), e um
    vetor paralelo guarda o rotulo (nome do deputado) de cada vertice.

    Esta classe nao conhece arquivos nem interface: apenas representa o grafo.

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao da classe a partir de grafoLista.py da aula.
"""

from grafoLista import Grafo as GrafoBase


class GrafoPonderadoND(GrafoBase):
    """Grafo nao orientado com peso na aresta, em lista de adjacencia."""

    TIPO = 2  # tipo do grafo conforme o enunciado

    # CONSTRUTOR
    def __init__(self, n=0):
        """Cria um grafo com n vertices sem rotulo e sem arestas."""
        super().__init__(n)          # aproveita n, m e listaAdj da classe da aula
        self.rotulos = ["" for _ in range(n)]

    # VERTICES
    def insereV(self, rotulo=""):
        """Insere um novo vertice no final e devolve o seu indice."""
        self.listaAdj.append([])
        self.rotulos.append(rotulo)
        self.n += 1
        return self.n - 1

    def removeV(self, v):
        """
        Remove o vertice v e todas as arestas incidentes a ele.
        Os vertices seguintes sao renumerados (descem uma posicao).
        """
        if not self.existeV(v):
            return False

        # remove v da lista dos seus vizinhos e desconta essas arestas
        for (vizinho, _peso) in self.listaAdj[v]:
            if vizinho != v:
                self.listaAdj[vizinho] = [
                    (w, p) for (w, p) in self.listaAdj[vizinho] if w != v
                ]
            self.m -= 1

        # apaga a lista e o rotulo do proprio v
        del self.listaAdj[v]
        del self.rotulos[v]
        self.n -= 1

        self._renumerar(v)
        return True

    def _renumerar(self, v):
        """Apos remover v, todo vizinho w > v passa a ser w - 1."""
        for i in range(self.n):
            self.listaAdj[i] = [
                (w - 1 if w > v else w, p) for (w, p) in self.listaAdj[i]
            ]

    def existeV(self, v):
        """Informa se v e um indice de vertice valido."""
        return isinstance(v, int) and 0 <= v < self.n

    def rotulo(self, v):
        """Devolve o rotulo do vertice v, ou uma marca caso nao exista."""
        return self.rotulos[v] if self.existeV(v) else "?"

    # ARESTAS
    def insereA(self, v, w, peso=1):
        """
        Insere a aresta {v, w} com o peso informado, nos dois sentidos.
        Se a aresta ja existe, apenas atualiza o peso.
        """
        if not (self.existeV(v) and self.existeV(w)):
            return False
        if v == w:
            return False  # lacos nao fazem sentido nesta modelagem

        if self.existeA(v, w):
            self._atualizaPeso(v, w, peso)
            return True

        self.listaAdj[v].append((w, peso))
        self.listaAdj[w].append((v, peso))
        self.m += 1
        return True

    def removeA(self, v, w):
        """Remove a aresta {v, w} nos dois sentidos."""
        if not self.existeA(v, w):
            return False

        self.listaAdj[v] = [(x, p) for (x, p) in self.listaAdj[v] if x != w]
        self.listaAdj[w] = [(x, p) for (x, p) in self.listaAdj[w] if x != v]
        self.m -= 1
        return True

    def existeA(self, v, w):
        """Informa se existe aresta entre v e w."""
        if not (self.existeV(v) and self.existeV(w)):
            return False
        return any(x == w for (x, _p) in self.listaAdj[v])

    def peso(self, v, w):
        """Devolve o peso da aresta {v, w}, ou None se ela nao existir."""
        if not self.existeV(v):
            return None
        for (x, p) in self.listaAdj[v]:
            if x == w:
                return p
        return None

    def arestas(self):
        """
        Devolve a lista de arestas como tuplas (v, w, peso), sem repetir.
        Cada aresta aparece uma unica vez, sempre com v < w.
        """
        resultado = []
        for v in range(self.n):
            for (w, p) in self.listaAdj[v]:
                if v < w:
                    resultado.append((v, w, p))
        return resultado

    # CONSULTAS
    def vizinhos(self, v):
        """Devolve a lista de tuplas (vizinho, peso) do vertice v."""
        return list(self.listaAdj[v]) if self.existeV(v) else []

    def grau(self, v):
        """Devolve o grau do vertice v."""
        return len(self.listaAdj[v]) if self.existeV(v) else 0

    def buscarPorRotulo(self, texto):
        """Devolve os indices cujos rotulos contem o texto informado."""
        alvo = texto.strip().lower()
        return [v for v in range(self.n) if alvo in self.rotulos[v].lower()]

    # EXIBICAO
    def show(self, inicio=0, fim=None):
        """
        Mostra o grafo como lista de adjacencia, do vertice 'inicio' ate
        'fim' (exclusivo). Sem argumentos, mostra o grafo inteiro.
        """
        if fim is None:
            fim = self.n

        print(f"\n n: {self.n:4d}   m: {self.m:5d}")
        print(" (lista de adjacencia - vizinho:peso)\n")

        for v in range(inicio, min(fim, self.n)):
            print(f"{v:4d} [{self.rotulos[v]}]: ", end="")
            if not self.listaAdj[v]:
                print("-", end="")
            for (w, p) in sorted(self.listaAdj[v]):
                print(f"{w}:{p}  ", end="")
            print()

        print("\nfim da impressao do grafo.")