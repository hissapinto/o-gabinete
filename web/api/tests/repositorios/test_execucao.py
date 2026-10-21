"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_execucao.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/execucao.py. O cenario tem duas execucoes de 2024
    e uma de 2023, justamente para verificar o DISTINCT da listagem de anos e
    a escolha da execucao mais recente.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from repositorios.execucao import buscar_execucao_mais_recente, listar_anos_disponiveis
from tests import cenario


def test_lista_anos_do_mais_recente_ao_mais_antigo(conexao):
    assert listar_anos_disponiveis(conexao) == [
        {"ano": cenario.ANO},
        {"ano": cenario.ANO_ANTERIOR},
    ]


def test_ano_com_duas_execucoes_aparece_uma_vez(conexao):
    anos = [linha["ano"] for linha in listar_anos_disponiveis(conexao)]
    assert anos.count(cenario.ANO) == 1


def test_execucao_mais_recente_e_a_de_maior_id(conexao):
    assert buscar_execucao_mais_recente(conexao, cenario.ANO) == cenario.EXECUCAO_ATUAL


def test_ano_sem_execucao_devolve_none(conexao):
    assert buscar_execucao_mais_recente(conexao, cenario.ANO_SEM_EXECUCAO) is None
