"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_cors.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    CORS configuravel por CORS_ORIGINS: a leitura da lista e o padrao sem
    CORS, que e o caso do compose e do Render (mesma origem).
"""

import pytest


@pytest.fixture
def origens_cors(cliente):
    """
    main so pode ser importado depois do fixture cliente, que define a
    DATABASE_URL de teste (ver conftest.py).
    """
    from main import origens_cors

    return origens_cors


def test_lista_de_origens_e_separada_por_virgula(origens_cors):
    assert origens_cors(" https://a.com, https://b.com/ ,,") == ["https://a.com", "https://b.com"]


def test_valor_vazio_nao_libera_origem(origens_cors):
    assert origens_cors("") == []


def test_sem_cors_origins_a_api_nao_manda_cabecalho_de_cors(cliente):
    resposta = cliente.get("/health", headers={"Origin": "https://outro-site.test"})

    assert resposta.status_code == 200
    assert "access-control-allow-origin" not in resposta.headers
