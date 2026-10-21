"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_anos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da rota GET /anos, que alimenta o seletor de ano da interface.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from tests import cenario


def test_lista_os_anos_com_execucao(cliente):
    resposta = cliente.get("/anos")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "anos": [{"ano": cenario.ANO}, {"ano": cenario.ANO_ANTERIOR}]
    }
