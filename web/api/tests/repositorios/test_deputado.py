"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_deputado.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/deputado.py. O foco esta no CASE de
    listar_mais_similares: como o banco guarda cada par uma vez so, com o
    menor id em deputado_a, o deputado pedido pode estar de qualquer um dos
    dois lados, e a consulta tem de devolver sempre "o outro" do par.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from repositorios.deputado import buscar_ficha, listar_mais_similares
from tests import cenario


def similares(conexao, deputado_id, limite=10):
    return listar_mais_similares(conexao, cenario.EXECUCAO_ATUAL, deputado_id, limite)


def ids(linhas):
    return [linha["deputado_id"] for linha in linhas]


# --- ficha -----------------------------------------------------------------

def test_ficha_traz_os_dados_cadastrais(conexao):
    ficha = buscar_ficha(conexao, cenario.ANA)

    assert ficha == {
        "deputado_id": cenario.ANA,
        "nome": cenario.NOMES[cenario.ANA],
        "sigla_partido": "PT",
        "sigla_uf": "SP",
        "url_foto": "https://exemplo.test/ana.jpg",
    }


def test_ficha_de_id_inexistente_devolve_none(conexao):
    assert buscar_ficha(conexao, 999999) is None


# --- mais similares --------------------------------------------------------

def test_deputado_do_lado_a_do_par_recebe_o_outro(conexao):
    """Ana e deputado_a em todos os seus pares."""
    assert ids(similares(conexao, cenario.ANA)) == cenario.SIMILARES_DE_ANA


def test_deputado_do_lado_b_do_par_recebe_o_outro(conexao):
    """
    Bruno e deputado_b no par com Ana e deputado_a no par com Carla. Se o CASE
    estivesse errado, uma das duas pontas sumiria da lista.
    """
    assert ids(similares(conexao, cenario.BRUNO)) == cenario.SIMILARES_DE_BRUNO


def test_nunca_devolve_o_proprio_deputado(conexao):
    for deputado_id in (cenario.ANA, cenario.BRUNO, cenario.CARLA):
        assert deputado_id not in ids(similares(conexao, deputado_id))


def test_ordena_do_maior_percentual_para_o_menor(conexao):
    percentuais = [float(linha["percentual"]) for linha in similares(conexao, cenario.ANA)]

    assert percentuais == sorted(percentuais, reverse=True)


def test_empate_de_percentual_e_desempatado_pelo_nome(conexao):
    """
    Alberto, Beatriz e Bruno empatam em 60.00 com Ana. Sao tres de
    proposito: com dois, a ordem alfabetica coincidiria com a ordem por id
    crescente ou com a decrescente, e o teste passaria mesmo se o criterio
    fosse o id.
    """
    linhas = similares(conexao, cenario.ANA)
    empatados = [linha for linha in linhas if str(linha["percentual"]) == "60.00"]

    assert [linha["nome"] for linha in empatados] == cenario.EMPATADOS_COM_ANA


def test_traz_o_percentual_e_as_votacoes_em_comum_do_par(conexao):
    por_id = {linha["deputado_id"]: linha for linha in similares(conexao, cenario.ANA)}
    em_comum, _, percentual = cenario.PARES[(cenario.ANA, cenario.BRUNO)]

    assert str(por_id[cenario.BRUNO]["percentual"]) == percentual
    assert por_id[cenario.BRUNO]["votacoes_em_comum"] == em_comum


def test_quem_ficou_fora_do_grafo_tem_lista_vazia(conexao):
    """Diego votou em 2024, mas nao entrou em nenhum par calculado."""
    assert similares(conexao, cenario.DIEGO) == []


def test_limite_corta_a_lista(conexao):
    assert ids(similares(conexao, cenario.ANA, limite=1)) == [cenario.CARLA]


def test_usa_apenas_a_execucao_pedida(conexao):
    """
    Na execucao antiga so existe o par Ana/Bruno, com 100.00. Se a consulta
    ignorasse o execucao_id, Carla apareceria aqui.
    """
    linhas = listar_mais_similares(conexao, cenario.EXECUCAO_ANTIGA, cenario.ANA, 10)

    assert ids(linhas) == [cenario.BRUNO]
    assert str(linhas[0]["percentual"]) == "100.00"
