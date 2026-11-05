"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_similaridade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da RN01 do lado do pipeline: Obstrucao conta como voto contra,
    Abstencao e Artigo 17 ficam fora da conta, e so entram as votacoes em que
    os dois votaram.

    Esta suite tem um papel que nenhuma outra cumpre. A mesma regra existe em
    dois lugares -- aqui, que gera os contadores gravados em app.concordancia,
    e em web/api/repositorios/voto.py, que lista as votacoes por tras desses
    contadores. Se as duas divergirem, a tela mostra uma lista que nao bate
    com o percentual ao lado dela, e nenhum erro aparece.

    Por isso o cenario abaixo e deliberadamente o mesmo de
    web/api/tests/cenario.py, com os mesmos votos e os mesmos numeros
    esperados: 5 votacoes em comum, 3 concordancias, 60.00%. Se um dos lados
    mudar de regra sem o outro, um dos dois quebra.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

import numpy as np
import pandas as pd
import pytest

from similaridade import (
    VALOR_VOTO,
    concordancia,
    contar_pares,
    matriz_de_votos,
    pares_com_concordancia,
)

ANA, BRUNO, CARLA = 100, 200, 300

# O mesmo cenario de web/api/tests/cenario.py, para o par Ana e Bruno.
VOTOS_DO_CENARIO = [
    ("v1", ANA, "Sim"),       ("v1", BRUNO, "Sim"),        # concordam
    ("v2", ANA, "Não"),       ("v2", BRUNO, "Não"),        # concordam
    ("v3", ANA, "Não"),       ("v3", BRUNO, "Obstrução"),  # concordam pela RN01
    ("v4", ANA, "Sim"),       ("v4", BRUNO, "Não"),        # divergem
    ("v5", ANA, "Não"),       ("v5", BRUNO, "Sim"),        # divergem
    ("v6", ANA, "Abstenção"), ("v6", BRUNO, "Sim"),        # fora da conta
    ("v7", ANA, "Sim"),       ("v7", BRUNO, "Artigo 17"),  # fora da conta
]

# Numeros que o cenario da API grava em app.concordancia para esse par.
EM_COMUM_ESPERADO = 5
CONCORDANCIAS_ESPERADAS = 3
PERCENTUAL_ESPERADO = 60.0


def df(votos):
    return pd.DataFrame(votos, columns=["idVotacao", "deputado_id", "voto"])


@pytest.fixture
def matriz():
    return matriz_de_votos(df(VOTOS_DO_CENARIO))


# --- a regra ---------------------------------------------------------------

def test_obstrucao_vale_o_mesmo_que_nao():
    """E a RN01 em uma linha: obstruir e votar contra."""
    assert VALOR_VOTO["Obstrução"] == VALOR_VOTO["Não"] == -1
    assert VALOR_VOTO["Sim"] == 1


def test_abstencao_e_artigo_17_nao_tem_valor():
    assert "Abstenção" not in VALOR_VOTO
    assert "Artigo 17" not in VALOR_VOTO


# --- matriz de votos -------------------------------------------------------

def test_voto_sem_valor_vira_zero(matriz):
    """Abstencao e Artigo 17 entram como 0, que e o mesmo que nao ter votado."""
    assert matriz.loc[ANA, "v6"] == 0
    assert matriz.loc[BRUNO, "v7"] == 0


def test_votacao_ausente_vira_zero():
    m = matriz_de_votos(df([("v1", ANA, "Sim"), ("v1", BRUNO, "Sim"), ("v2", ANA, "Não")]))

    assert m.loc[BRUNO, "v2"] == 0


def test_deputado_sem_nenhum_voto_valido_sai_da_matriz():
    m = matriz_de_votos(df([
        ("v1", ANA, "Sim"), ("v1", BRUNO, "Sim"),
        ("v1", CARLA, "Abstenção"), ("v2", CARLA, "Artigo 17"),
    ]))

    assert CARLA not in m.index
    assert sorted(m.index) == [ANA, BRUNO]


# --- contadores ------------------------------------------------------------

def test_conta_so_as_votacoes_em_que_os_dois_votaram(matriz):
    em_comum, _ = contar_pares(matriz)
    i, j = list(matriz.index).index(ANA), list(matriz.index).index(BRUNO)

    assert int(em_comum[i, j]) == EM_COMUM_ESPERADO


def test_contadores_sao_simetricos(matriz):
    em_comum, saldo = contar_pares(matriz)

    assert np.array_equal(em_comum, em_comum.T)
    assert np.array_equal(saldo, saldo.T)


# --- percentual ------------------------------------------------------------

def test_percentual_do_par_do_cenario(matriz):
    C = concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO)

    assert C.loc[ANA, BRUNO] == pytest.approx(PERCENTUAL_ESPERADO)


def test_concordancia_total_da_cem(matriz):
    iguais = matriz_de_votos(df([
        ("v1", ANA, "Sim"), ("v1", BRUNO, "Sim"),
        ("v2", ANA, "Não"), ("v2", BRUNO, "Obstrução"),
    ]))
    C = concordancia(iguais, minimo_em_comum=2)

    assert C.loc[ANA, BRUNO] == pytest.approx(100.0)


def test_discordancia_total_da_zero():
    opostos = matriz_de_votos(df([
        ("v1", ANA, "Sim"), ("v1", BRUNO, "Não"),
        ("v2", ANA, "Não"), ("v2", BRUNO, "Sim"),
    ]))
    C = concordancia(opostos, minimo_em_comum=2)

    assert C.loc[ANA, BRUNO] == pytest.approx(0.0)


def test_diagonal_fica_sem_valor(matriz):
    C = concordancia(matriz, minimo_em_comum=1)

    assert np.isnan(C.loc[ANA, ANA])


def test_par_abaixo_do_minimo_fica_sem_valor(matriz):
    C = concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO + 1)

    assert np.isnan(C.loc[ANA, BRUNO])


def test_percentual_fica_entre_zero_e_cem(matriz):
    C = concordancia(matriz, minimo_em_comum=1).to_numpy()
    valores = C[~np.isnan(C)]

    assert valores.min() >= 0
    assert valores.max() <= 100


# --- pares para a carga ----------------------------------------------------

def test_par_do_cenario_bate_com_o_da_api(matriz):
    """
    Os numeros que este teste espera sao os mesmos que
    web/api/tests/cenario.py grava em app.concordancia. Se este teste quebrar
    sem que o cenario da API tenha mudado, as duas implementacoes da RN01
    divergiram.
    """
    pares = pares_com_concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO)
    linha = pares[(pares["deputado_a"] == ANA) & (pares["deputado_b"] == BRUNO)].iloc[0]

    assert int(linha["votacoes_em_comum"]) == EM_COMUM_ESPERADO
    assert int(linha["concordancias"]) == CONCORDANCIAS_ESPERADAS


def test_percentual_do_banco_decorre_dos_contadores(matriz):
    """
    O banco calcula o percentual como concordancias * 100 / votacoes_em_comum,
    em coluna gerada. Aqui se confere que essa conta bate com a matriz.
    """
    pares = pares_com_concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO)
    linha = pares.iloc[0]
    C = concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO)

    do_banco = linha["concordancias"] * 100.0 / linha["votacoes_em_comum"]
    assert do_banco == pytest.approx(C.loc[linha["deputado_a"], linha["deputado_b"]])


def test_par_vem_com_o_menor_id_primeiro(matriz):
    """O banco exige deputado_a < deputado_b, por CHECK na tabela."""
    pares = pares_com_concordancia(matriz, minimo_em_comum=1)

    assert (pares["deputado_a"] < pares["deputado_b"]).all()


def test_menor_id_vem_primeiro_mesmo_com_a_matriz_fora_de_ordem(matriz):
    """
    A matriz vinda de matriz_de_votos ja tem o indice em ordem crescente, e
    com ela a normalizacao do par passaria despercebida. Aqui a matriz e
    reordenada de proposito, para exercitar de fato o min/max.
    """
    invertida = matriz.loc[[BRUNO, ANA]]

    pares = pares_com_concordancia(invertida, minimo_em_comum=1)

    assert int(pares.iloc[0]["deputado_a"]) == ANA
    assert int(pares.iloc[0]["deputado_b"]) == BRUNO


def test_cada_par_aparece_uma_vez_so():
    m = matriz_de_votos(df([
        (v, d, "Sim") for v in ("v1", "v2") for d in (ANA, BRUNO, CARLA)
    ]))
    pares = pares_com_concordancia(m, minimo_em_comum=1)

    assert len(pares) == 3, "tres deputados formam tres pares"
    assert not pares.duplicated(subset=["deputado_a", "deputado_b"]).any()


def test_par_abaixo_do_minimo_nao_entra(matriz):
    pares = pares_com_concordancia(matriz, minimo_em_comum=EM_COMUM_ESPERADO + 1)

    assert pares.empty


def test_colunas_esperadas_pela_carga(matriz):
    pares = pares_com_concordancia(matriz, minimo_em_comum=1)

    assert list(pares.columns) == [
        "deputado_a", "deputado_b", "votacoes_em_comum", "concordancias",
    ]


def test_concordancias_nunca_passam_das_votacoes_em_comum(matriz):
    """O banco tem CHECK (concordancias <= votacoes_em_comum)."""
    pares = pares_com_concordancia(matriz, minimo_em_comum=1)

    assert (pares["concordancias"] <= pares["votacoes_em_comum"]).all()
