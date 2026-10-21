"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_concordancia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/concordancia.py: os contadores do par, o
    percentual que o proprio banco calcula e o isolamento entre execucoes.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from repositorios.concordancia import buscar_concordancia
from tests import cenario


def test_contadores_e_percentual_do_par(conexao):
    em_comum, concordancias, percentual = cenario.PARES[(cenario.ANA, cenario.BRUNO)]

    par = buscar_concordancia(conexao, cenario.EXECUCAO_ATUAL, cenario.ANA, cenario.BRUNO)

    assert par["votacoes_em_comum"] == em_comum
    assert par["concordancias"] == concordancias
    assert str(par["percentual"]) == percentual


def test_percentual_e_calculado_pelo_banco(conexao):
    """O percentual e coluna gerada, entao nao pode divergir dos contadores."""
    par = buscar_concordancia(conexao, cenario.EXECUCAO_ATUAL, cenario.BRUNO, cenario.CARLA)

    esperado = round(par["concordancias"] * 100 / par["votacoes_em_comum"], 2)
    assert float(par["percentual"]) == esperado


def test_cada_execucao_tem_seus_proprios_numeros(conexao):
    """
    O mesmo par aparece nas duas execucoes de 2024 com numeros diferentes.
    A consulta tem de devolver o da execucao pedida, e nao misturar as duas.
    """
    atual = buscar_concordancia(conexao, cenario.EXECUCAO_ATUAL, cenario.ANA, cenario.BRUNO)
    antiga = buscar_concordancia(conexao, cenario.EXECUCAO_ANTIGA, cenario.ANA, cenario.BRUNO)

    assert str(atual["percentual"]) == "60.00"
    assert str(antiga["percentual"]) == "100.00"


def test_par_sem_linha_calculada_devolve_none(conexao):
    assert buscar_concordancia(
        conexao, cenario.EXECUCAO_ATUAL, cenario.ANA, cenario.DIEGO
    ) is None
