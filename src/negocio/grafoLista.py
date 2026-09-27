"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/negocio/grafoLista.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Classe Grafo em lista de adjacencia, disponibilizada pelo professor na
    disciplina de Teoria dos Grafos (codigo original de icalc, criado em
    14/02/2023). Serve de classe base para o GrafoPonderadoND (grafo.py),
    que acrescenta pesos e rotulos.

Historico de alteracoes:
    24/09/2026 - Isabela - Inclusao do codigo da aula no projeto.
"""

# Grafo como uma lista de adjacência
class Grafo:
    TAM_MAX_DEFAULT = 100 # qtde de vértices máxima default
    # construtor da classe grafo
    def __init__(self, n=TAM_MAX_DEFAULT):
        self.n = n # número de vértices
        self.m = 0 # número de arestas
        # lista de adjacência
        self.listaAdj = [[] for i in range(self.n)]
        
    # Insere uma aresta no Grafo tal que
    # v é adjacente a w
    def insereA(self, v, w):
        self.listaAdj[v].append(w)
        self.m+=1
     
    # remove uma aresta v->w do Grafo	
    def removeA(self, v, w):
        self.listaAdj[v].remove(w)
        self.m-=1
        
    # Apresenta o Grafo contendo
    # número de vértices, arestas
    # e a LISTA de adjacência obtida	
    def show(self):
        print(f"\n n: {self.n:2d} ", end="")
        print(f"m: {self.m:2d}")
        for i in range(self.n):
            print(f"\n{i:2d}: ", end="")
            for w in range(len(self.listaAdj[i])):
                val = self.listaAdj[i][w]
                print(f"{val:2d}", end="") 

        print("\n\nfim da impressao do grafo." )