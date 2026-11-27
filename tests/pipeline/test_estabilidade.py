"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_estabilidade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da analise de estabilidade dos blocos entre anos
    (pipeline/estabilidade.py) e da tabela de deputados de cada ano
    (processamento.deputados_do_ano). Usam dados de brinquedo, sem baixar
    nada, para que o resultado esperado possa ser conferido na leitura.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

import pandas as pd
import pytest

import estabilidade as est
from processamento import deputados_do_ano


# NOMEAR OS BLOCOS
def test_nomear_blocos_governo_oposicao_e_terceiro():
    grupos = [[1, 2, 3, 4], [5, 6, 7], [8, 9]]
    gov = {1: 90, 2: 85, 3: 95, 4: 80, 5: 30, 6: 35, 7: 25, 8: 20, 9: 15}
    opo = {1: 30, 2: 35, 3: 25, 4: 40, 5: 90, 6: 85, 7: 95, 8: 97, 9: 99}
    # o bloco [8, 9] vota mais com a Oposicao, mas o maior e o [5, 6, 7]
    assert est.nomear_blocos(grupos, 3, gov, opo) == ["Governo", "Oposição", "Terceiro"]


def test_nomear_blocos_governo_nao_precisa_ser_o_maior():
    grupos = [[1, 2, 3, 4], [5, 6]]
    gov = {1: 20, 2: 25, 3: 30, 4: 20, 5: 90, 6: 95}
    opo = {1: 90, 2: 85, 3: 80, 4: 95, 5: 30, 6: 20}
    assert est.nomear_blocos(grupos, 2, gov, opo) == ["Oposição", "Governo"]


def test_nomear_blocos_terceiro_que_vota_com_o_governo():
    """Como o PSOL em 2023 e 2024: bloco a parte, mas perto do Governo."""
    grupos = [[1, 2, 3], [4, 5], [6, 7]]
    gov = {1: 90, 2: 88, 3: 92, 4: 30, 5: 25, 6: 80, 7: 82}
    opo = {1: 40, 2: 45, 3: 35, 4: 90, 5: 92, 6: 20, 7: 18}
    assert est.nomear_blocos(grupos, 3, gov, opo) == ["Governo", "Oposição", "Terceiro"]


def test_nomear_blocos_grupos_alem_dos_significativos_sao_avulsos():
    grupos = [[1, 2], [3, 4], [5]]
    gov = {1: 90, 2: 90, 3: 20, 4: 20, 5: 50}
    opo = {1: 20, 2: 20, 3: 90, 4: 90, 5: 50}
    assert est.nomear_blocos(grupos, 2, gov, opo) == ["Governo", "Oposição", "Avulso"]


def test_nomear_blocos_sem_alinhamento_de_oposicao():
    """Nenhum outro bloco vota mais com a Oposicao: nao inventa uma Oposicao."""
    grupos = [[1, 2], [3, 4]]
    gov = {1: 90, 2: 90, 3: 70, 4: 70}
    opo = {1: 20, 2: 20, 3: 40, 4: 40}
    assert est.nomear_blocos(grupos, 2, gov, opo) == ["Governo", "Terceiro"]


# COMPARACAO ENTRE ANOS
def test_transicoes_so_conta_quem_esta_nos_dois_anos():
    antes = {"1": "Governo", "2": "Governo", "3": "Oposição", "4": "Oposição"}
    depois = {"1": "Governo", "2": "Oposição", "3": "Oposição", "5": "Governo"}
    assert est.transicoes(antes, depois) == {("Governo", "Governo"): 1, ("Governo", "Oposição"): 1,
                                             ("Oposição", "Oposição"): 1}


def test_rand_ajustado_divisoes_iguais_vale_1():
    assert est.indice_rand_ajustado(list("aabbcc"), list("aabbcc")) == pytest.approx(1.0)


def test_rand_ajustado_nao_depende_do_nome_dos_grupos():
    x = ["Gov", "Gov", "Opo", "Opo", "PSOL"]
    y = ["B1", "B1", "B2", "B2", "B3"]
    assert est.indice_rand_ajustado(x, y) == pytest.approx(1.0)


def test_rand_ajustado_valor_conhecido():
    # exemplo classico: tabela de contingencia [[2, 1], [0, 2]]
    x = ["a", "a", "a", "b", "b"]
    y = ["p", "p", "q", "q", "q"]
    # soma dos pares = 1 + 1 = 2; esperado = (3 + 1) * (1 + 3) / 10 = 1,6; maximo = 4
    assert est.indice_rand_ajustado(x, y) == pytest.approx((2 - 1.6) / (4 - 1.6))


def test_rand_ajustado_exige_mesmo_tamanho():
    with pytest.raises(ValueError):
        est.indice_rand_ajustado(["a", "b"], ["a"])


# GRAFO DE UM ANO
def test_grafo_do_ano_separa_dois_grupos_e_descarta_quem_nao_tem_par():
    votacoes = [f"v{i}" for i in range(40)]
    linhas = []
    for dep, grupo in ((1, "A"), (2, "A"), (3, "A"), (4, "B"), (5, "B"), (6, "B")):
        for k, v in enumerate(votacoes):
            sim = (k % 2 == 0) if grupo == "A" else (k % 2 == 1)
            linhas.append({"idVotacao": v, "deputado_id": dep, "voto": "Sim" if sim else "Não"})
    # deputado 7 votou so 5 vezes: nenhum par chega a 30 votacoes em comum
    linhas += [{"idVotacao": v, "deputado_id": 7, "voto": "Sim"} for v in votacoes[:5]]
    votos = pd.DataFrame(linhas)
    deputados = pd.DataFrame({
        "deputado_id": range(1, 8),
        "deputado_nome": ["Ana", "Bia", "Cris", "Davi", "Edu", "Fabi", "Gil"],
        "deputado_siglaPartido": ["PT", "PT", "PT", "PL", "PL", "PL", "PSD"],
        "deputado_siglaUf": ["SP"] * 7,
    })
    ids, g, fora = est.grafo_do_ano(votos, deputados)
    assert fora == 1
    assert sorted(ids) == [1, 2, 3, 4, 5, 6]
    # concordam 100% dentro do grupo e 0% entre grupos: so arestas internas
    lado = {i: (i <= 3) for i in ids}
    for v, w, peso in g.arestas():
        assert lado[ids[v]] == lado[ids[w]]
        assert peso == 100


# PARTIDO DE CADA ANO
def test_deputados_do_ano_usa_o_partido_do_voto_mais_recente():
    df = pd.DataFrame({
        "idVotacao": ["v1", "v2", "v3"],
        "dataHoraVoto": ["2026-02-01T10:00:00", "2026-05-01T10:00:00", "2026-03-01T10:00:00"],
        "deputado_id": [10, 10, 20],
        "deputado_nome": ["Ana", "Ana", "Bia"],
        "deputado_siglaPartido": ["UNIÃO", "PL", "PT"],
        "deputado_siglaUf": ["SP", "SP", "RJ"],
    })
    tabela = deputados_do_ano(df)
    assert tabela.set_index("deputado_id")["deputado_siglaPartido"].to_dict() == {10: "PL", 20: "PT"}
    assert list(tabela.columns) == ["deputado_id", "deputado_nome", "deputado_siglaPartido", "deputado_siglaUf"]
