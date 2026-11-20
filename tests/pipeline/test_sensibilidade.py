"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_sensibilidade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes das funcoes da analise de sensibilidade (pipeline/sensibilidade.py)
    e da validacao com as orientacoes de bancada (pipeline/alinhamento_governo.py).
    Usam uma Camara de brinquedo com dois grupos bem definidos, para que o
    resultado esperado possa ser conferido na leitura, sem baixar dados.

Historico de alteracoes:
    20/11/2026 - Kaique - Criacao.
"""

import numpy as np
import pandas as pd
import pytest

import alinhamento_governo as ag
import sensibilidade as sens


@pytest.fixture
def camara():
    """
    Seis deputados: tres do PSOL que concordam 98% entre si e tres do PL que
    concordam 96% entre si; entre os grupos, 40%. A diagonal fica NaN, como
    na matriz real.
    """
    rotulos = ["Ana (PSOL-SP)", "Bia (PSOL-RJ)", "Cris (PSOL-MG)",
               "Davi (PL-SP)", "Edu (PL-RJ)", "Fabi (PL-MG)"]
    C = np.full((6, 6), 40.0)
    C[np.ix_([0, 1, 2], [0, 1, 2])] = 98.0
    C[np.ix_([3, 4, 5], [3, 4, 5])] = 96.0
    np.fill_diagonal(C, np.nan)
    return C, rotulos


# --- sensibilidade ---------------------------------------------------------

def test_ordem_alfabetica_ignora_acento_e_maiuscula():
    assert sens.ordem_alfabetica(["Édson", "carla", "Bruno"]) == [2, 1, 0]


def test_montar_liga_so_os_mais_parecidos_acima_do_limiar(camara):
    C, rotulos = camara

    g = sens.montar(C, rotulos, list(range(6)), k=2, minimo=75)

    assert g.n == 6
    assert g.m == 6, "dois triangulos: cada grupo fica fechado em si"
    assert not g.existeA(0, 3)


def test_montar_respeita_a_ordem_dos_vertices(camara):
    C, rotulos = camara
    ordem = [5, 4, 3, 2, 1, 0]

    g = sens.montar(C, rotulos, ordem, k=2, minimo=75)

    assert g.rotulos == rotulos[::-1]


def test_limiar_alto_tira_todas_as_arestas(camara):
    C, rotulos = camara

    g = sens.montar(C, rotulos, list(range(6)), k=2, minimo=99)

    assert g.m == 0


def test_medir_reconhece_o_psol_isolado(camara):
    C, rotulos = camara
    g = sens.montar(C, rotulos, list(range(6)), k=2, minimo=75)

    m = sens.medir(g)

    assert m["componentes"] == 2
    assert m["tamanhos"] == [3, 3]
    assert m["psol_isolado"] is True
    assert m["q_blocos"] == pytest.approx(0.5)


def test_medir_com_psol_ligado_ao_resto(camara):
    C, rotulos = camara
    C = C.copy()
    C[2, 3] = C[3, 2] = 99.0          # uma ponte forte entre os grupos
    g = sens.montar(C, rotulos, list(range(6)), k=2, minimo=75)

    assert sens.medir(g)["psol_isolado"] is False


# --- alinhamento com as orientacoes ----------------------------------------

@pytest.fixture
def votos():
    return pd.DataFrame({
        "idVotacao":   [1, 1, 2, 2, 3, 3],
        "deputado_id": [10, 20, 10, 20, 10, 20],
        "voto":        ["Sim", "Não", "Não", "Obstrução", "Sim", "Abstenção"],
    })


def test_orientacoes_ignora_liberado_e_trata_obstrucao_como_contra():
    df = pd.DataFrame({
        "idVotacao":    [1, 2, 3, 3],
        "siglaBancada": ["Governo", "Governo", "Governo", "Oposição"],
        "orientacao":   ["Sim", "Obstrução", "Liberado", "Sim"],
    })

    o = ag.orientacoes(df, "Governo")

    assert o.to_dict() == {1: 1, 2: -1}


def test_alinhamento_conta_so_votacoes_orientadas_e_votadas(votos):
    orient = pd.Series({1: 1, 2: -1, 3: 1})

    a = ag.alinhamento(votos, orient, minimo=1).set_index("deputado_id")

    # deputado 10: Sim/Sim, Nao/Nao, Sim/Sim -> 3 de 3
    assert a.loc[10, "alinhamento"] == pytest.approx(100.0)
    assert a.loc[10, "votacoes"] == 3
    # deputado 20: Nao x Sim, Obstrucao = Nao igual; a abstencao fica fora -> 1 de 2
    assert a.loc[20, "alinhamento"] == pytest.approx(50.0)
    assert a.loc[20, "votacoes"] == 2


def test_alinhamento_abaixo_do_minimo_fica_sem_valor(votos):
    a = ag.alinhamento(votos, pd.Series({1: 1, 2: -1, 3: 1}), minimo=3).set_index("deputado_id")

    assert np.isnan(a.loc[20, "alinhamento"])


def test_resumo_por_grupo():
    alin = pd.Series({1: 90.0, 2: 80.0, 3: np.nan, 4: 30.0})

    linhas = ag.resumo_por_grupo(alin, [[1, 2, 3], [4]], ["A", "B"])

    assert linhas[0][:4] == ("A", 3, pytest.approx(85.0), pytest.approx(85.0))
    assert linhas[1][2] == pytest.approx(30.0)
