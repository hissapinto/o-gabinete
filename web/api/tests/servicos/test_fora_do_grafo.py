"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/servicos/test_fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de servicos/fora_do_grafo.py: o motivo de cada deputado, a
    resposta montada sobre o cenario e o ano sem execucao.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

import pytest

from servicos.erros import NaoEncontrado
from servicos.fora_do_grafo import motivo, obter_fora_do_grafo
from tests import cenario


@pytest.mark.parametrize("votacoes, artigo_17, esperado", [
    (9, 102, "presidencia"),      # como o presidente da Camara em 2024
    (1, 0, "poucas_votacoes"),
    (20, 11, "poucas_votacoes"),  # presidiu algumas sessoes, mas votou mais
    (0, 0, "poucas_votacoes"),
])
def test_motivo(votacoes, artigo_17, esperado):
    assert motivo(votacoes, artigo_17) == esperado


def test_resposta_do_ano(conexao):
    resposta = obter_fora_do_grafo(conexao, cenario.ANO)

    assert resposta["ano"] == cenario.ANO
    assert resposta["total_votacoes"] == 7
    assert resposta["minimo_em_comum"] == 3
    assert [d["deputado_id"] for d in resposta["deputados"]] == [cenario.DIEGO]
    assert resposta["deputados"][0]["motivo"] == "poucas_votacoes"


def test_ano_sem_execucao_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado):
        obter_fora_do_grafo(conexao, cenario.ANO_SEM_EXECUCAO)
