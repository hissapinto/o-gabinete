"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_logica_grafos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes dos algoritmos de analise do grafo: componentes conexas, conexidade
    e vertices isolados. Sao o conteudo avaliado em Teoria dos Grafos, e a
    busca em largura por tras deles usa a FilaCircular da aula.

    Os grafos de teste sao montados a mao, pequenos o bastante para o
    resultado esperado ser obvio na leitura.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

from grafo import GrafoPonderadoND
from logica_grafos import componentes_conexas, eh_conexo, vertices_isolados


def montar(n, arestas):
    g = GrafoPonderadoND(n)
    for (v, w) in arestas:
        g.insereA(v, w, 1)
    return g


# --- componentes conexas ---------------------------------------------------

def test_caminho_simples_e_uma_componente_so():
    g = montar(4, [(0, 1), (1, 2), (2, 3)])

    assert componentes_conexas(g) == [[0, 1, 2, 3]]


def test_duas_ilhas_sao_duas_componentes():
    g = montar(5, [(0, 1), (2, 3)])

    assert componentes_conexas(g) == [[0, 1], [2, 3], [4]]


def test_vertice_sem_aresta_e_componente_de_um():
    g = montar(3, [(0, 1)])

    assert componentes_conexas(g) == [[0, 1], [2]]


def test_cada_componente_vem_ordenada():
    """A busca em largura visita fora de ordem; a saida tem de ser previsivel."""
    g = montar(4, [(3, 0), (0, 2), (2, 1)])

    assert componentes_conexas(g) == [[0, 1, 2, 3]]


def test_nenhum_vertice_aparece_em_duas_componentes():
    g = montar(6, [(0, 1), (1, 2), (3, 4)])
    componentes = componentes_conexas(g)

    todos = [v for c in componentes for v in c]
    assert sorted(todos) == list(range(6))
    assert len(todos) == len(set(todos))


def test_ciclo_nao_faz_a_busca_repetir_vertice():
    g = montar(3, [(0, 1), (1, 2), (2, 0)])

    assert componentes_conexas(g) == [[0, 1, 2]]


def test_grafo_sem_vertices_nao_tem_componente():
    assert componentes_conexas(GrafoPonderadoND(0)) == []


# --- conexidade ------------------------------------------------------------

def test_grafo_ligado_e_conexo():
    assert eh_conexo(montar(3, [(0, 1), (1, 2)])) is True


def test_grafo_partido_nao_e_conexo():
    assert eh_conexo(montar(4, [(0, 1), (2, 3)])) is False


def test_um_vertice_sozinho_e_conexo():
    assert eh_conexo(montar(1, [])) is True


def test_grafo_sem_vertices_nao_e_conexo():
    """Sem vertice nao ha o que ligar, entao a resposta e nao."""
    assert eh_conexo(GrafoPonderadoND(0)) is False


def test_vertice_isolado_quebra_a_conexidade():
    g = montar(3, [(0, 1)])

    assert eh_conexo(g) is False


# --- vertices isolados -----------------------------------------------------

def test_lista_os_vertices_sem_aresta():
    g = montar(5, [(0, 1), (1, 2)])

    assert vertices_isolados(g) == [3, 4]


def test_grafo_conexo_nao_tem_isolado():
    assert vertices_isolados(montar(3, [(0, 1), (1, 2)])) == []


def test_grafo_sem_arestas_tem_todos_isolados():
    assert vertices_isolados(montar(3, [])) == [0, 1, 2]
