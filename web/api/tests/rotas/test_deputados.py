"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_deputados.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da rota GET /anos/{ano}/deputados/{deputado_id}, que abre o cartao
    de perfil. Cobre os tres desfechos e a validacao do parametro limite,
    que o FastAPI faz a partir da assinatura da funcao.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

import pytest

from tests import cenario


def url(deputado_id, ano=cenario.ANO):
    return f"/anos/{ano}/deputados/{deputado_id}"


def test_ficha_com_a_lista_de_similares(cliente):
    resposta = cliente.get(url(cenario.ANA))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["deputado"]["nome"] == cenario.NOMES[cenario.ANA]
    assert [s["deputado_id"] for s in corpo["mais_similares"]] == cenario.SIMILARES_DE_ANA


def test_quem_ficou_fora_do_grafo_devolve_200_com_lista_vazia(cliente):
    resposta = cliente.get(url(cenario.DIEGO))

    assert resposta.status_code == 200
    assert resposta.json()["mais_similares"] == []


def test_deputado_que_nao_votou_devolve_404(cliente):
    resposta = cliente.get(url(cenario.ELENA))

    assert resposta.status_code == 404
    assert str(cenario.ELENA) in resposta.json()["detail"]


def test_id_inexistente_devolve_404(cliente):
    assert cliente.get(url(999999)).status_code == 404


def test_ano_sem_grafo_devolve_404(cliente):
    assert cliente.get(url(cenario.ANA, ano=cenario.ANO_SEM_EXECUCAO)).status_code == 404


def test_limite_corta_a_lista(cliente):
    corpo = cliente.get(f"{url(cenario.ANA)}?limite=1").json()

    assert len(corpo["mais_similares"]) == 1


@pytest.mark.parametrize("limite", [0, -1, 51])
def test_limite_fora_da_faixa_devolve_422(cliente, limite):
    """A faixa 1..50 esta na assinatura da rota; o FastAPI valida sozinho."""
    assert cliente.get(f"{url(cenario.ANA)}?limite={limite}").status_code == 422


def test_limite_nao_numerico_devolve_422(cliente):
    assert cliente.get(f"{url(cenario.ANA)}?limite=muitos").status_code == 422
