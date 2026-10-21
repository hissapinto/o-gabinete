"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_concordancias.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da rota GET /anos/{ano}/concordancias/{deputado_a}/{deputado_b},
    aberta pelo clique na aresta e na lista de mais similares. Cobre as duas
    listas, o filtro por tipo, o limite opcional e as validacoes: par igual
    da 422, tipo fora da lista da 422, limite menor que 1 da 422.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

import pytest

from tests import cenario


def url(a=cenario.ANA, b=cenario.BRUNO, ano=cenario.ANO):
    return f"/anos/{ano}/concordancias/{a}/{b}"


def votacoes(bloco):
    return [item["votacao_id"] for item in bloco["itens"]]


def test_par_traz_contadores_e_as_duas_listas(cliente):
    em_comum, concordancias, percentual = cenario.PARES[(cenario.ANA, cenario.BRUNO)]
    resposta = cliente.get(url())

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "completo"
    assert corpo["votacoes_em_comum"] == em_comum
    assert corpo["concordancias"] == concordancias
    assert float(corpo["percentual"]) == float(percentual)
    assert votacoes(corpo["listas"]["concordancias"]) == cenario.ANA_BRUNO_CONCORDARAM
    assert votacoes(corpo["listas"]["divergencias"]) == cenario.ANA_BRUNO_DIVERGIRAM


def test_item_traz_o_voto_literal_de_cada_um(cliente):
    """
    A tela precisa do voto escrito, e nao so do rotulo: um par Nao/Obstrucao
    aparece como concordancia, e sem os votos a vista pareceria erro.
    """
    corpo = cliente.get(url()).json()
    por_votacao = {i["votacao_id"]: i for i in corpo["listas"]["concordancias"]["itens"]}

    assert por_votacao["v3"]["voto_a"] == "Não"
    assert por_votacao["v3"]["voto_b"] == "Obstrução"
    assert por_votacao["v3"]["concordaram"] is True


def test_soma_dos_totais_e_o_votacoes_em_comum(cliente):
    corpo = cliente.get(url()).json()
    listas = corpo["listas"]

    assert (
        listas["concordancias"]["total"] + listas["divergencias"]["total"]
        == corpo["votacoes_em_comum"]
    )


def test_ordem_dos_ids_na_url_nao_importa(cliente):
    direta = cliente.get(url(cenario.ANA, cenario.BRUNO)).json()
    invertida = cliente.get(url(cenario.BRUNO, cenario.ANA)).json()

    assert direta == invertida


def test_sem_limite_as_listas_vem_inteiras(cliente):
    listas = cliente.get(url()).json()["listas"]

    assert listas["limite"] is None
    assert len(listas["concordancias"]["itens"]) == listas["concordancias"]["total"]


def test_limite_corta_cada_lista_sem_mudar_os_totais(cliente):
    listas = cliente.get(f"{url()}?limite=1").json()["listas"]

    assert len(listas["concordancias"]["itens"]) == 1
    assert listas["concordancias"]["total"] == 3


@pytest.mark.parametrize(
    "tipo,preenchida,nula",
    [("concordancia", "concordancias", "divergencias"),
     ("divergencia", "divergencias", "concordancias")],
)
def test_tipo_preenche_so_a_lista_pedida(cliente, tipo, preenchida, nula):
    listas = cliente.get(f"{url()}?tipo={tipo}").json()["listas"]

    assert listas["tipo"] == tipo
    assert listas[nula] is None
    assert listas[preenchida] is not None


def test_par_sem_dados_suficientes_devolve_200(cliente):
    resposta = cliente.get(url(cenario.ANA, cenario.DIEGO))

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "insuficiente"


def test_deputado_que_nao_votou_devolve_404(cliente):
    assert cliente.get(url(cenario.ANA, cenario.ELENA)).status_code == 404


def test_ano_sem_grafo_devolve_404(cliente):
    assert cliente.get(url(ano=cenario.ANO_SEM_EXECUCAO)).status_code == 404


def test_dois_ids_iguais_devolve_422(cliente):
    resposta = cliente.get(url(cenario.ANA, cenario.ANA))

    assert resposta.status_code == 422
    assert "diferentes" in resposta.json()["detail"]


def test_tipo_invalido_devolve_422(cliente):
    """A faixa de valores esta no Literal da assinatura da rota."""
    assert cliente.get(f"{url()}?tipo=banana").status_code == 422


@pytest.mark.parametrize("limite", [0, -5])
def test_limite_menor_que_um_devolve_422(cliente, limite):
    assert cliente.get(f"{url()}?limite={limite}").status_code == 422


def test_offset_negativo_devolve_422(cliente):
    assert cliente.get(f"{url()}?offset=-1").status_code == 422
