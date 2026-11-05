"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes do GrafoPonderadoND, a estrutura que representa o grafo em lista de
    adjacencia. Por ser nao orientado, cada aresta existe nas duas listas mas
    conta uma vez so em m: e a invariante que mais aparece aqui.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

import pytest

from grafo import GrafoPonderadoND


@pytest.fixture
def triangulo():
    """Tres vertices rotulados, todos ligados entre si."""
    g = GrafoPonderadoND(3)
    g.rotulos = ["Ana", "Bruno", "Carla"]
    g.insereA(0, 1, 90)
    g.insereA(1, 2, 80)
    g.insereA(0, 2, 70)
    return g


# --- vertices --------------------------------------------------------------

def test_grafo_novo_nao_tem_aresta():
    g = GrafoPonderadoND(4)

    assert g.n == 4
    assert g.m == 0
    assert g.arestas() == []


def test_insere_vertice_no_fim_e_devolve_o_indice():
    g = GrafoPonderadoND(2)

    assert g.insereV("Novo") == 2
    assert g.n == 3
    assert g.rotulo(2) == "Novo"


def test_indice_invalido_nao_existe():
    g = GrafoPonderadoND(2)

    assert not g.existeV(-1)
    assert not g.existeV(2)
    assert g.rotulo(99) == "?"


# --- arestas ---------------------------------------------------------------

def test_aresta_vale_nos_dois_sentidos_e_conta_uma_vez(triangulo):
    assert triangulo.existeA(0, 1)
    assert triangulo.existeA(1, 0)
    assert triangulo.m == 3


def test_peso_e_o_mesmo_nos_dois_sentidos(triangulo):
    assert triangulo.peso(0, 1) == 90
    assert triangulo.peso(1, 0) == 90


def test_inserir_aresta_existente_atualiza_o_peso(triangulo):
    triangulo.insereA(0, 1, 55)

    assert triangulo.peso(0, 1) == 55
    assert triangulo.peso(1, 0) == 55
    assert triangulo.m == 3, "atualizar peso nao cria aresta nova"


def test_laco_e_recusado():
    g = GrafoPonderadoND(2)

    assert g.insereA(0, 0, 10) is False
    assert g.m == 0


def test_aresta_com_vertice_inexistente_e_recusada():
    g = GrafoPonderadoND(2)

    assert g.insereA(0, 5, 10) is False
    assert g.m == 0


def test_peso_de_aresta_inexistente_e_none():
    g = GrafoPonderadoND(2)

    assert g.peso(0, 1) is None


def test_remove_aresta_dos_dois_lados(triangulo):
    assert triangulo.removeA(0, 1) is True

    assert not triangulo.existeA(0, 1)
    assert not triangulo.existeA(1, 0)
    assert triangulo.m == 2


def test_remover_aresta_inexistente_nao_altera_nada(triangulo):
    assert triangulo.removeA(0, 0) is False
    assert triangulo.m == 3


def test_lista_de_arestas_nao_repete_o_par(triangulo):
    arestas = triangulo.arestas()

    assert len(arestas) == triangulo.m
    assert all(v < w for (v, w, _p) in arestas)


# --- remocao de vertice ----------------------------------------------------

def test_remove_vertice_e_renumera_os_seguintes(triangulo):
    """
    Tira Bruno (indice 1). Sobram Ana e Carla, e a aresta entre eles: Carla,
    que era 2, passa a ser 1.
    """
    assert triangulo.removeV(1) is True

    assert triangulo.n == 2
    assert triangulo.rotulos == ["Ana", "Carla"]
    assert triangulo.m == 1
    assert triangulo.arestas() == [(0, 1, 70)]


def test_remover_vertice_inexistente_nao_altera_nada(triangulo):
    assert triangulo.removeV(9) is False
    assert triangulo.n == 3
    assert triangulo.m == 3


def test_remover_vertice_isolado_nao_mexe_nas_arestas():
    g = GrafoPonderadoND(3)
    g.rotulos = ["Ana", "Bruno", "Sozinha"]
    g.insereA(0, 1, 50)

    g.removeV(2)

    assert g.n == 2
    assert g.m == 1
    assert g.arestas() == [(0, 1, 50)]


# --- consultas -------------------------------------------------------------

def test_vizinhos_traz_par_de_vizinho_e_peso(triangulo):
    assert sorted(triangulo.vizinhos(0)) == [(1, 90), (2, 70)]


def test_vizinhos_de_vertice_inexistente_e_lista_vazia(triangulo):
    assert triangulo.vizinhos(99) == []


def test_grau_conta_as_arestas_incidentes(triangulo):
    assert triangulo.grau(0) == 2
    assert triangulo.grau(99) == 0


def test_busca_por_rotulo_ignora_maiusculas_e_acha_trecho(triangulo):
    assert triangulo.buscarPorRotulo("an") == [0]
    assert triangulo.buscarPorRotulo("BRUNO") == [1]
    assert triangulo.buscarPorRotulo("zzz") == []
