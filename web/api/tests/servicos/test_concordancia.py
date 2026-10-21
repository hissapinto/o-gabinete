"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/servicos/test_concordancia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de servicos/concordancia.py: a normalizacao da ordem do par, os
    tres desfechos (nao encontrado, insuficiente e completo), as duas listas
    com os totais corretos e a distincao entre lista vazia e lista nao
    pedida, que vem como None.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

import pytest

from servicos.concordancia import obter_concordancia
from servicos.erros import NaoEncontrado
from tests import cenario


def concordancia_de_ana_e_bruno(conexao, tipo="todas", limite=None, offset=0):
    return obter_concordancia(
        conexao, cenario.ANO, cenario.ANA, cenario.BRUNO, tipo, limite, offset
    )


def votacoes(bloco):
    return [item["votacao_id"] for item in bloco["itens"]]


# --- contadores ------------------------------------------------------------

def test_contadores_do_par(conexao):
    em_comum, concordancias, percentual = cenario.PARES[(cenario.ANA, cenario.BRUNO)]
    resultado = concordancia_de_ana_e_bruno(conexao)

    assert resultado["status"] == "completo"
    assert resultado["votacoes_em_comum"] == em_comum
    assert resultado["concordancias"] == concordancias
    assert resultado["divergencias"] == em_comum - concordancias
    assert str(resultado["percentual"]) == percentual


def test_ordem_dos_ids_nao_importa(conexao):
    direta = obter_concordancia(
        conexao, cenario.ANO, cenario.ANA, cenario.BRUNO, "todas", None, 0
    )
    invertida = obter_concordancia(
        conexao, cenario.ANO, cenario.BRUNO, cenario.ANA, "todas", None, 0
    )

    assert direta == invertida


def test_usa_a_execucao_mais_recente_do_ano(conexao):
    """Na execucao antiga o mesmo par aparece com 100.00."""
    assert str(concordancia_de_ana_e_bruno(conexao)["percentual"]) == "60.00"


# --- as duas listas --------------------------------------------------------

def test_lista_as_concordancias_e_as_divergencias(conexao):
    listas = concordancia_de_ana_e_bruno(conexao)["listas"]

    assert votacoes(listas["concordancias"]) == cenario.ANA_BRUNO_CONCORDARAM
    assert votacoes(listas["divergencias"]) == cenario.ANA_BRUNO_DIVERGIRAM


def test_totais_das_listas_batem_com_os_contadores(conexao):
    resultado = concordancia_de_ana_e_bruno(conexao)
    listas = resultado["listas"]

    assert listas["concordancias"]["total"] == resultado["concordancias"]
    assert listas["divergencias"]["total"] == resultado["divergencias"]


def test_soma_dos_totais_e_o_votacoes_em_comum(conexao):
    """
    Os totais vem dos contadores de app.concordancia, nao de um COUNT. Se as
    duas contas divergirem, a paginacao mente sobre quantas paginas existem.
    """
    resultado = concordancia_de_ana_e_bruno(conexao)
    listas = resultado["listas"]

    assert (
        listas["concordancias"]["total"] + listas["divergencias"]["total"]
        == resultado["votacoes_em_comum"]
    )


def test_totais_nao_mudam_com_o_limite(conexao):
    sem_limite = concordancia_de_ana_e_bruno(conexao)["listas"]
    com_limite = concordancia_de_ana_e_bruno(conexao, limite=1)["listas"]

    assert com_limite["concordancias"]["total"] == sem_limite["concordancias"]["total"]
    assert len(com_limite["concordancias"]["itens"]) == 1


def test_sem_limite_as_listas_vem_inteiras(conexao):
    listas = concordancia_de_ana_e_bruno(conexao, limite=None)["listas"]

    assert len(listas["concordancias"]["itens"]) == listas["concordancias"]["total"]
    assert len(listas["divergencias"]["itens"]) == listas["divergencias"]["total"]


def test_offset_avanca_em_cada_lista(conexao):
    listas = concordancia_de_ana_e_bruno(conexao, limite=2, offset=2)["listas"]

    assert votacoes(listas["concordancias"]) == ["v1"]
    assert votacoes(listas["divergencias"]) == [], "a lista de 2 itens se esgota antes"


# --- o filtro por tipo -----------------------------------------------------

def test_tipo_concordancia_anula_a_outra_lista(conexao):
    listas = concordancia_de_ana_e_bruno(conexao, tipo="concordancia")["listas"]

    assert listas["divergencias"] is None
    assert votacoes(listas["concordancias"]) == cenario.ANA_BRUNO_CONCORDARAM


def test_tipo_divergencia_anula_a_outra_lista(conexao):
    listas = concordancia_de_ana_e_bruno(conexao, tipo="divergencia")["listas"]

    assert listas["concordancias"] is None
    assert votacoes(listas["divergencias"]) == cenario.ANA_BRUNO_DIVERGIRAM


def test_tipo_aparece_na_resposta(conexao):
    assert concordancia_de_ana_e_bruno(conexao, tipo="divergencia")["listas"]["tipo"] == (
        "divergencia"
    )


# --- desfechos -------------------------------------------------------------

def test_par_sem_dados_suficientes(conexao):
    """
    Diego votou em 2024, mas o par com Ana nao foi calculado. Nao e 404: os
    dois existem e votaram, so nao ha concordancia a mostrar.
    """
    resultado = obter_concordancia(
        conexao, cenario.ANO, cenario.ANA, cenario.DIEGO, "todas", None, 0
    )

    assert resultado["status"] == "insuficiente"
    assert resultado["votacoes_em_comum"] is None
    assert resultado["percentual"] is None
    assert resultado["listas"]["concordancias"]["itens"] == []
    assert resultado["listas"]["divergencias"]["itens"] == []


def test_insuficiente_tem_as_mesmas_chaves_de_completo(conexao):
    completo = concordancia_de_ana_e_bruno(conexao)
    insuficiente = obter_concordancia(
        conexao, cenario.ANO, cenario.ANA, cenario.DIEGO, "todas", None, 0
    )

    assert set(completo) == set(insuficiente)
    assert set(completo["listas"]) == set(insuficiente["listas"])


def test_ano_sem_grafo_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado, match=str(cenario.ANO_SEM_EXECUCAO)):
        obter_concordancia(
            conexao, cenario.ANO_SEM_EXECUCAO, cenario.ANA, cenario.BRUNO, "todas", None, 0
        )


def test_deputado_sem_voto_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado, match=str(cenario.ELENA)):
        obter_concordancia(
            conexao, cenario.ANO, cenario.ANA, cenario.ELENA, "todas", None, 0
        )


def test_erro_nomeia_os_dois_quando_nenhum_votou(conexao):
    with pytest.raises(NaoEncontrado) as erro:
        obter_concordancia(
            conexao, cenario.ANO, cenario.ELENA, 999999, "todas", None, 0
        )

    assert str(cenario.ELENA) in str(erro.value)
    assert "999999" in str(erro.value)
