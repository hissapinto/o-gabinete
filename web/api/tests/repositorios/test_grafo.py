"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/grafo.py: os nos saem de app.concordancia, de
    qualquer um dos dois lados do par, e as arestas saem de app.aresta mas
    com o percentual vindo de app.concordancia pelo JOIN.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from repositorios.grafo import listar_arestas, listar_nos
from tests import cenario


# --- nos -------------------------------------------------------------------

def test_nos_sao_os_deputados_com_par_calculado(conexao):
    nos = listar_nos(conexao, cenario.EXECUCAO_ATUAL)

    assert [no["deputado_id"] for no in nos] == cenario.NOS_DO_GRAFO


def test_nos_vem_em_ordem_alfabetica_de_nome(conexao):
    nomes = [no["nome"] for no in listar_nos(conexao, cenario.EXECUCAO_ATUAL)]

    assert nomes == sorted(nomes)


def test_deputado_fora_de_qualquer_par_nao_e_no(conexao):
    ids = [no["deputado_id"] for no in listar_nos(conexao, cenario.EXECUCAO_ATUAL)]

    assert cenario.DIEGO not in ids, "Diego votou mas nao tem par calculado"
    assert cenario.ELENA not in ids, "Elena nunca votou"


def test_no_traz_partido_e_uf_mas_nao_a_foto(conexao):
    """A foto so e usada na ficha; o grafo nao a carrega."""
    no = listar_nos(conexao, cenario.EXECUCAO_ATUAL)[0]

    assert set(no) == {"deputado_id", "nome", "sigla_partido", "sigla_uf"}


def test_cada_deputado_aparece_uma_vez_so(conexao):
    """Ana esta em tres pares; o UNION nao pode repeti-la."""
    ids = [no["deputado_id"] for no in listar_nos(conexao, cenario.EXECUCAO_ATUAL)]

    assert len(ids) == len(set(ids))


def test_execucao_sem_concordancia_nao_tem_nos(conexao):
    assert listar_nos(conexao, cenario.EXECUCAO_2023) == []


# --- arestas ---------------------------------------------------------------

def test_arestas_vem_em_ordem_de_par(conexao):
    arestas = listar_arestas(conexao, cenario.EXECUCAO_ATUAL)

    assert [(a["deputado_a"], a["deputado_b"]) for a in arestas] == cenario.ARESTAS_DO_GRAFO


def test_aresta_traz_o_percentual_da_concordancia_e_nao_o_peso(conexao):
    """
    No cenario os pesos de app.aresta sao diferentes dos percentuais de
    proposito. A aresta tem de mostrar o mesmo numero da ficha e do detalhe
    do par, que vem de app.concordancia.
    """
    por_par = {
        (a["deputado_a"], a["deputado_b"]): str(a["percentual"])
        for a in listar_arestas(conexao, cenario.EXECUCAO_ATUAL)
    }

    for par, (_, _, percentual) in cenario.PARES.items():
        if par in por_par:
            assert por_par[par] == percentual


def test_execucao_sem_aresta_devolve_lista_vazia(conexao):
    assert listar_arestas(conexao, cenario.EXECUCAO_2023) == []


def test_aresta_de_outra_execucao_nao_vaza(conexao):
    """A execucao antiga tem uma aresta so; a atual tem tres."""
    assert len(listar_arestas(conexao, cenario.EXECUCAO_ANTIGA)) == 1
    assert len(listar_arestas(conexao, cenario.EXECUCAO_ATUAL)) == len(
        cenario.ARESTAS_DO_GRAFO
    )
