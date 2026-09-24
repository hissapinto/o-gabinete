"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/negocio/logica_grafos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Algoritmos de analise sobre o grafo. Nao guarda dados: recebe um objeto
    GrafoPonderadoND, percorre a estrutura e devolve o resultado.

    Implementa a busca em largura (usando a FilaCircular vista em aula) para
    determinar a conexidade do grafo nao orientado e listar as componentes
    conexas.

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao, adaptando conexidade_nao_direcionado para
                         lista de adjacencia.
"""

from filaCircular import FilaCircular


def componentes_conexas(grafo):
    """
    Devolve a lista de componentes conexas do grafo.
    Cada componente e uma lista de indices de vertices, em ordem crescente.
    Usa busca em largura com a FilaCircular apresentada em aula.
    """
    visitados = [False] * grafo.n
    componentes = []

    for origem in range(grafo.n):
        if visitados[origem]:
            continue

        # nova componente: percorre tudo que alcanca a partir de 'origem'
        atual = []
        fila = FilaCircular(grafo.n + 1)
        visitados[origem] = True
        fila.enqueue(origem)

        while not fila.isEmpty():
            v = fila.dequeue()
            atual.append(v)
            for (w, _peso) in grafo.vizinhos(v):
                if not visitados[w]:
                    visitados[w] = True
                    fila.enqueue(w)

        componentes.append(sorted(atual))

    return componentes


def eh_conexo(grafo):
    """Informa se o grafo nao orientado e conexo."""
    if grafo.n == 0:
        return False
    return len(componentes_conexas(grafo)) == 1


def vertices_isolados(grafo):
    """Devolve os vertices sem nenhuma aresta incidente."""
    return [v for v in range(grafo.n) if grafo.grau(v) == 0]