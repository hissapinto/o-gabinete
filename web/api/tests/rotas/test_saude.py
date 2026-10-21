"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_saude.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes das rotas do main.py: /health, que nao toca no banco, e
    /deputados, que lista os cadastrados. A /health existe justamente para
    separar "a API nao subiu" de "a consulta falhou".

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from tests import cenario


def test_health_responde_sem_tocar_no_banco(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "servico": "backend"}


def test_lista_todos_os_deputados_cadastrados(cliente):
    resposta = cliente.get("/deputados")

    assert resposta.status_code == 200
    ids = [d["deputado_id"] for d in resposta.json()]
    assert set(ids) == set(cenario.NOMES)


def test_deputados_vem_em_ordem_alfabetica(cliente):
    nomes = [d["nome"] for d in cliente.get("/deputados").json()]

    assert nomes == sorted(nomes)
