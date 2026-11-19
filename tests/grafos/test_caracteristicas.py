"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_caracteristicas.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes das caracteristicas do grafo (opcoes k a n do menu): grau dos
    vertices, grafo euleriano, grafo hamiltoniano com articulacoes e pontes,
    e coloracao por Welsh-Powell com maior clique. Usa grafos classicos
    (ciclo, caminho, estrela, completo, bipartido completo e o grafo de
    Petersen), cujas respostas sao conhecidas da teoria.

Historico de alteracoes:
    19/11/2026 - Isabela - Criacao.
"""

import pytest

from grafo import GrafoPonderadoND
import caracteristicas as car


def montar(n, arestas):
    g = GrafoPonderadoND(n)
    for (v, w) in arestas:
        g.insereA(v, w, 90)
    return g


def ciclo(n):
    return montar(n, [(i, (i + 1) % n) for i in range(n)])


def caminho(n):
    return montar(n, [(i, i + 1) for i in range(n - 1)])


def completo(n):
    return montar(n, [(i, j) for i in range(n) for j in range(i + 1, n)])


def estrela(folhas):
    return montar(folhas + 1, [(0, i) for i in range(1, folhas + 1)])


def petersen():
    """Grafo de Petersen: 3-regular, nao hamiltoniano e com numero cromatico 3."""
    externo = [(i, (i + 1) % 5) for i in range(5)]
    raios = [(i, i + 5) for i in range(5)]
    interno = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    return montar(10, externo + raios + interno)


# --- grau ------------------------------------------------------------------

def test_resumo_de_graus_da_estrela():
    resumo = car.resumo_graus(estrela(4))

    assert resumo["minimo"] == 1
    assert resumo["maximo"] == 4
    assert resumo["medio"] == pytest.approx(8 / 5)
    assert resumo["mediano"] == 1
    assert resumo["distribuicao"] == {1: 4, 4: 1}
    assert resumo["maiores"][0] == (0, 4)


def test_soma_dos_graus_e_o_dobro_das_arestas():
    g = petersen()

    assert car.resumo_graus(g)["soma"] == 2 * g.m


def test_quantidade_de_vertices_impares_e_sempre_par():
    for g in (estrela(3), caminho(5), petersen(), completo(4)):
        assert car.resumo_graus(g)["impares"] % 2 == 0


def test_mediana_com_quantidade_par_de_vertices():
    assert car.resumo_graus(caminho(4))["mediano"] == 1.5


def test_grafo_vazio_nao_tem_resumo():
    assert car.resumo_graus(GrafoPonderadoND(0)) is None


def test_faixas_somam_todos_os_vertices():
    resumo = car.resumo_graus(petersen())
    faixas = car.faixas_de_grau(resumo["distribuicao"])

    assert sum(q for (_t, q) in faixas) == 10


# --- euleriano -------------------------------------------------------------

def test_ciclo_e_euleriano():
    assert car.analise_euleriana(ciclo(5))["classificacao"] == "euleriano"


def test_caminho_e_semi_euleriano():
    analise = car.analise_euleriana(caminho(4))

    assert analise["classificacao"] == "semi-euleriano"
    assert analise["impares"] == [0, 3]


def test_estrela_com_3_folhas_nao_e_euleriana():
    analise = car.analise_euleriana(estrela(3))

    assert analise["classificacao"] == "nao euleriano"
    assert analise["arestas_faltantes"] == 2


def test_dois_ciclos_separados_nao_sao_eulerianos():
    g = montar(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])

    analise = car.analise_euleriana(g)

    assert analise["classificacao"] == "nao euleriano"
    assert analise["componentes_com_aresta"] == 2


def test_vertice_isolado_nao_impede_ciclo_euleriano():
    g = montar(4, [(0, 1), (1, 2), (2, 0)])  # vertice 3 isolado

    assert car.analise_euleriana(g)["classificacao"] == "euleriano"


def test_grafo_sem_arestas_nao_e_euleriano():
    assert car.analise_euleriana(montar(3, []))["classificacao"] == "nao euleriano"


# --- articulacoes e pontes -------------------------------------------------

def test_caminho_tem_articulacoes_internas_e_so_pontes():
    articulacoes, pontes = car.articulacoes_e_pontes(caminho(4))

    assert articulacoes == [1, 2]
    assert [(v, w) for (v, w, _p) in pontes] == [(0, 1), (1, 2), (2, 3)]


def test_ciclo_nao_tem_articulacao_nem_ponte():
    assert car.articulacoes_e_pontes(ciclo(6)) == ([], [])


def test_dois_triangulos_unidos_por_um_vertice():
    """Gravata-borboleta: o vertice 2 e a unica articulacao, e nao ha ponte."""
    g = montar(5, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)])

    assert car.articulacoes_e_pontes(g) == ([2], [])


def test_raiz_com_dois_filhos_e_articulacao():
    assert car.articulacoes_e_pontes(estrela(3))[0] == [0]


# --- hamiltoniano ----------------------------------------------------------

def test_completo_e_hamiltoniano_por_dirac():
    analise = car.analise_hamiltoniana(completo(5))

    assert analise["classificacao"] == "hamiltoniano"
    assert "Dirac" in analise["motivo"]


def test_caminho_nao_tem_ciclo_e_percurso_fica_inconclusivo():
    analise = car.analise_hamiltoniana(caminho(5))

    assert analise["classificacao"] == "nao hamiltoniano"
    assert "grau >= 2" in analise["motivo"]
    assert analise["percurso"] == "inconclusivo pelas condicoes verificadas"


def test_estrela_nao_admite_percurso_hamiltoniano():
    analise = car.analise_hamiltoniana(estrela(3))

    assert analise["percurso"].startswith("nao admite")


def test_desconexo_nao_e_hamiltoniano():
    g = montar(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])

    analise = car.analise_hamiltoniana(g)

    assert analise["classificacao"] == "nao hamiltoniano"
    assert "desconexo" in analise["percurso"]


def test_petersen_nao_e_hamiltoniano_pela_busca_exaustiva():
    """Petersen passa por todas as condicoes necessarias e nao tem ciclo."""
    analise = car.analise_hamiltoniana(petersen())

    assert all(ok for (_nome, ok) in analise["necessarias"])
    assert analise["classificacao"] == "nao hamiltoniano"
    assert "busca exaustiva" in analise["motivo"]


def test_busca_exaustiva_devolve_ciclo_valido():
    """Ciclo de 8 com duas cordas: nem Dirac nem Ore valem, mas ha ciclo."""
    g = ciclo(8)
    g.insereA(0, 4, 90)
    g.insereA(2, 6, 90)

    analise = car.analise_hamiltoniana(g)
    rota = analise["ciclo"]

    assert analise["classificacao"] == "hamiltoniano"
    assert sorted(rota[:-1]) == list(range(8)) and rota[0] == rota[-1]
    assert all(g.existeA(rota[i], rota[i + 1]) for i in range(8))


# --- coloracao -------------------------------------------------------------

@pytest.mark.parametrize("g, cromatico", [
    (completo(5), 5),
    (ciclo(6), 2),
    (ciclo(5), 3),
    (estrela(4), 2),
    (petersen(), 3),
])
def test_coloracao_valida_e_com_o_numero_certo_de_cores(g, cromatico):
    analise = car.analise_coloracao(g)

    assert analise["valida"]
    assert analise["num_cores"] == cromatico
    assert analise["limite_inferior"] <= cromatico <= analise["limite_superior"]


def test_bipartido_completo_usa_duas_cores():
    k33 = montar(6, [(i, j) for i in range(3) for j in range(3, 6)])

    analise = car.analise_coloracao(k33)

    assert analise["bipartido"]
    assert analise["exato"]


def test_coloracao_invalida_e_detectada():
    assert not car.coloracao_valida(caminho(3), [0, 0, 1])


def test_maior_clique():
    g = completo(4)
    g.insereV()
    g.insereA(3, 4, 90)  # vertice extra preso a clique de 4

    assert car.maior_clique(g) == [0, 1, 2, 3]


def test_maior_clique_de_grafo_sem_aresta_tem_um_vertice():
    assert len(car.maior_clique(montar(3, []))) == 1
