"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/servicos/test_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de servicos/grafo.py: usa a execucao mais recente do ano, ano sem
    execucao levanta NaoEncontrado e no sem posicao levanta LayoutAusente,
    em vez de voltar com x e y nulos ou inventados.
"""

import pytest

from servicos.erros import LayoutAusente, NaoEncontrado
from servicos.grafo import obter_grafo
from tests import cenario


def test_grafo_do_ano_traz_nos_com_posicao_e_arestas(conexao):
    grafo = obter_grafo(conexao, cenario.ANO)

    assert grafo["ano"] == cenario.ANO
    assert [no["deputado_id"] for no in grafo["nos"]] == cenario.NOS_DO_GRAFO
    assert {no["deputado_id"]: (no["x"], no["y"]) for no in grafo["nos"]} == cenario.POSICOES
    arestas = [(a["deputado_a"], a["deputado_b"]) for a in grafo["arestas"]]
    assert arestas == cenario.ARESTAS_DO_GRAFO


def test_ano_sem_execucao_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado):
        obter_grafo(conexao, cenario.ANO_SEM_EXECUCAO)


def test_no_sem_posicao_levanta_layout_ausente(conexao):
    with pytest.raises(LayoutAusente, match=f"ano {cenario.ANO_SEM_LAYOUT}.*rode a carga"):
        obter_grafo(conexao, cenario.ANO_SEM_LAYOUT)


def test_ano_com_execucao_mas_sem_concordancia_nao_exige_layout(conexao):
    """Grafo vazio nao tem no para posicionar: volta vazio, sem erro."""
    assert obter_grafo(conexao, cenario.ANO_ANTERIOR) == {
        "ano": cenario.ANO_ANTERIOR, "nos": [], "arestas": [],
    }
