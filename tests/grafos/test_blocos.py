"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_blocos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da solucao do problema (opcao j do menu): arvore geradora maxima
    por Kruskal, deteccao de blocos por corte da arvore, resumo dos blocos e
    modularidade. Os grafos sao pequenos e montados a mao, de modo que a
    resposta certa possa ser conferida na leitura.

Historico de alteracoes:
    19/11/2026 - Kaique - Criacao.
"""

import pytest

from grafo import GrafoPonderadoND
import blocos


def montar(n, arestas, rotulos=None):
    g = GrafoPonderadoND(n)
    if rotulos:
        g.rotulos = list(rotulos)
    for (v, w, p) in arestas:
        g.insereA(v, w, p)
    return g


@pytest.fixture
def dois_grupos():
    """
    Dois triangulos de alta concordancia (0-1-2 e 3-4-5) ligados por uma
    unica aresta fraca (2-3, peso 60). A divisao natural e {0,1,2} e {3,4,5}.
    """
    return montar(6, [
        (0, 1, 95), (1, 2, 90), (0, 2, 85),
        (3, 4, 97), (4, 5, 92), (3, 5, 88),
        (2, 3, 60),
    ], ["A (PT-SP)", "B (PT-RJ)", "C (PSB-MG)", "D (PL-SP)", "E (PL-RJ)", "F (PP-BA)"])


# --- conjuntos disjuntos ---------------------------------------------------

def test_uniao_de_conjuntos():
    c = blocos.ConjuntosDisjuntos(4)

    assert c.unir(0, 1) is True
    assert c.unir(2, 3) is True
    assert c.unir(1, 0) is False, "ja estavam juntos"
    assert c.encontrar(0) == c.encontrar(1)
    assert c.encontrar(0) != c.encontrar(2)


# --- arvore geradora maxima ------------------------------------------------

def test_arvore_tem_n_menos_1_arestas_e_peso_maximo(dois_grupos):
    arvore = blocos.arvore_geradora_maxima(dois_grupos)

    assert len(arvore) == dois_grupos.n - 1
    # os dois triangulos perdem a aresta mais fraca (85 e 88); a ponte 2-3 fica
    assert sorted(arvore) == [(0, 1, 95), (1, 2, 90), (2, 3, 60), (3, 4, 97), (4, 5, 92)]
    assert blocos.peso_total(arvore) == 434


def test_arvore_maxima_recusa_aresta_que_fecha_ciclo():
    """
    Quadrado com diagonal: o Kruskal aceita 50 (0-2) e 40 (3-0), recusa 30
    (2-3, fecharia o triangulo 0-2-3) e completa a arvore com 20 (1-2).
    """
    g = montar(4, [(0, 1, 10), (1, 2, 20), (2, 3, 30), (3, 0, 40), (0, 2, 50)])

    arvore = blocos.arvore_geradora_maxima(g)

    assert sorted(arvore) == [(0, 2, 50), (0, 3, 40), (1, 2, 20)]
    assert blocos.peso_total(arvore) == 110


def test_grafo_desconexo_gera_floresta():
    g = montar(5, [(0, 1, 90), (1, 2, 80), (3, 4, 70)])

    arvore = blocos.arvore_geradora_maxima(g)

    assert len(arvore) == 5 - 2, "uma arvore por componente: n - c arestas"


def test_arvore_sem_arestas_e_vazia():
    assert blocos.arvore_geradora_maxima(montar(3, [])) == []


def test_arvore_nao_fecha_ciclo():
    g = montar(3, [(0, 1, 100), (1, 2, 100), (0, 2, 100)])

    assert len(blocos.arvore_geradora_maxima(g)) == 2


# --- deteccao de blocos ----------------------------------------------------

def test_dois_blocos_cortam_a_aresta_fraca(dois_grupos):
    resultado = blocos.detectar_blocos(dois_grupos, 2, 2)

    assert resultado["cortes"] == [(2, 3, 60)]
    assert resultado["blocos"] == [[0, 1, 2], [3, 4, 5]]
    assert resultado["significativos"] == 2


def test_um_bloco_nao_corta_nada(dois_grupos):
    resultado = blocos.detectar_blocos(dois_grupos, 1, 1)

    assert resultado["cortes"] == []
    assert resultado["blocos"] == [[0, 1, 2, 3, 4, 5]]


def test_tamanho_minimo_impede_isolar_um_vertice():
    """
    Caminho 0-1-2-3-4-5 em que a aresta mais fraca (4-5) isolaria o vertice
    5. Com tamanho minimo 2 o corte vai para a aresta 2-3, a mais fraca que
    deixa os dois lados com pelo menos 2 vertices.
    """
    g = montar(6, [(0, 1, 99), (1, 2, 98), (2, 3, 80), (3, 4, 97), (4, 5, 50)])

    resultado = blocos.detectar_blocos(g, 2, 2)

    assert resultado["cortes"] == [(2, 3, 80)]
    assert resultado["blocos"] == [[0, 1, 2], [3, 4, 5]]


def test_sem_corte_valido_devolve_menos_blocos():
    g = montar(3, [(0, 1, 90), (1, 2, 80)])

    resultado = blocos.detectar_blocos(g, 3, 2)

    assert resultado["significativos"] == 1
    assert resultado["cortes"] == []


def test_componentes_ja_contam_como_blocos():
    g = montar(6, [(0, 1, 90), (1, 2, 90), (3, 4, 90), (4, 5, 90)])

    resultado = blocos.detectar_blocos(g, 2, 3)

    assert resultado["cortes"] == []
    assert resultado["significativos"] == 2


def test_vertice_isolado_vira_grupo_avulso_e_nao_conta():
    """O vertice 6 nao tem aresta: fica avulso, e os 2 blocos vem de corte."""
    g = montar(7, [(0, 1, 95), (1, 2, 95), (2, 3, 60), (3, 4, 95), (4, 5, 95)])

    resultado = blocos.detectar_blocos(g, 2, 3)

    assert resultado["significativos"] == 2
    assert resultado["blocos"] == [[0, 1, 2], [3, 4, 5], [6]]


def test_cada_vertice_fica_em_um_unico_bloco(dois_grupos):
    resultado = blocos.detectar_blocos(dois_grupos, 3, 1)
    todos = [v for b in resultado["blocos"] for v in b]

    assert sorted(todos) == list(range(dois_grupos.n))


@pytest.mark.parametrize("k, minimo", [(0, 1), (1, 0)])
def test_parametros_invalidos(dois_grupos, k, minimo):
    with pytest.raises(ValueError):
        blocos.detectar_blocos(dois_grupos, k, minimo)


# --- avaliacao -------------------------------------------------------------

@pytest.mark.parametrize("rotulo, partido", [
    ("Abilio Brunini (PL-MT)", "PL"),
    ("Adail Filho (REPUBLICANOS-AM)", "REPUBLICANOS"),
    ("Fausto Jr. (UNIÃO-AM)", "UNIÃO"),
    ("Deputado Teste", "?"),
])
def test_partido_do_rotulo(rotulo, partido):
    assert blocos.partido_do_rotulo(rotulo) == partido


def test_resumo_conta_partidos_e_arestas(dois_grupos):
    resumos = blocos.resumo_dos_blocos(dois_grupos, [[0, 1, 2], [3, 4, 5]])

    assert resumos[0]["tamanho"] == 3
    assert resumos[0]["partidos"] == [("PT", 2), ("PSB", 1)]
    assert resumos[0]["arestas_internas"] == 3
    assert resumos[0]["concordancia_media"] == pytest.approx(90.0)
    assert resumos[0]["arestas_externas"] == 1
    assert resumos[1]["partidos"] == [("PL", 2), ("PP", 1)]


def test_modularidade_da_divisao_natural_e_positiva(dois_grupos):
    natural = blocos.modularidade(dois_grupos, [[0, 1, 2], [3, 4, 5]])
    misturada = blocos.modularidade(dois_grupos, [[0, 3, 4], [1, 2, 5]])

    # 7 arestas, 3 internas em cada lado, soma de graus 7 em cada lado
    assert natural == pytest.approx(6 / 7 - 2 * (7 / 14) ** 2)
    assert natural > misturada


def test_modularidade_de_um_bloco_so_e_zero(dois_grupos):
    assert blocos.modularidade(dois_grupos, [list(range(6))]) == pytest.approx(0.0)


def test_blocos_por_partido(dois_grupos):
    assert blocos.blocos_por_partido(dois_grupos) == [[0, 1], [3, 4], [2], [5]]


def test_sensibilidade_tem_uma_linha_por_combinacao(dois_grupos):
    linhas = blocos.sensibilidade(dois_grupos, [1, 2], [1, 2])

    assert len(linhas) == 4
    assert {(l["num_blocos"], l["tamanho_minimo"]) for l in linhas} == {
        (1, 1), (2, 1), (1, 2), (2, 2)}
