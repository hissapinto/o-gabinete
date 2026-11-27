"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/fora_do_grafo.py sobre o cenario: em 2024, Diego
    votou so na v1 e nao tem par calculado; Elena nunca votou e nao aparece;
    quem esta no grafo tambem nao. Em 2023 a execucao nao tem nenhum par,
    entao todo mundo que votou fica fora.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

from repositorios.fora_do_grafo import (buscar_minimo_em_comum, contar_votacoes_do_ano,
                                        listar_fora_do_grafo)
from tests import cenario


def test_lista_so_quem_votou_e_ficou_fora(conexao):
    linhas = listar_fora_do_grafo(conexao, cenario.EXECUCAO_ATUAL, cenario.ANO)

    assert [l["deputado_id"] for l in linhas] == [cenario.DIEGO]


def test_conta_so_os_votos_da_rn01_e_o_artigo_17(conexao):
    (diego,) = listar_fora_do_grafo(conexao, cenario.EXECUCAO_ATUAL, cenario.ANO)

    assert diego == {"deputado_id": cenario.DIEGO, "nome": cenario.NOMES[cenario.DIEGO],
                     "sigla_partido": "PP", "sigla_uf": "BA", "votacoes": 1, "artigo_17": 0}


def test_quem_nunca_votou_nao_aparece(conexao):
    ids = {l["deputado_id"] for l in listar_fora_do_grafo(conexao, cenario.EXECUCAO_ATUAL, cenario.ANO)}

    assert cenario.ELENA not in ids


def test_execucao_sem_par_deixa_todos_que_votaram_de_fora(conexao):
    """2023 tem execucao sem concordancia; Ana e Bruno votaram na v8."""
    linhas = listar_fora_do_grafo(conexao, cenario.EXECUCAO_2023, cenario.ANO_ANTERIOR)

    # mesmo numero de votacoes: desempata pelo nome
    assert [l["deputado_id"] for l in linhas] == [cenario.ANA, cenario.BRUNO]


def test_execucao_antiga_nao_vale_para_a_atual(conexao):
    """Na execucao antiga so Ana e Bruno tem par; Beatriz, Carla, Alberto e Diego ficam fora."""
    ids = [l["deputado_id"] for l in listar_fora_do_grafo(conexao, cenario.EXECUCAO_ANTIGA, cenario.ANO)]

    assert set(ids) == {cenario.BEATRIZ, cenario.CARLA, cenario.ALBERTO, cenario.DIEGO}


def test_conta_as_votacoes_do_ano(conexao):
    assert contar_votacoes_do_ano(conexao, cenario.ANO) == 7
    assert contar_votacoes_do_ano(conexao, cenario.ANO_ANTERIOR) == 1


def test_minimo_em_comum_da_execucao(conexao):
    assert buscar_minimo_em_comum(conexao, cenario.EXECUCAO_ATUAL) == 3
