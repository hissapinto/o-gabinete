"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da rota GET /anos/{ano}/grafo, que alimenta a tela inicial
    inteira. Verifica tambem que o 404 do ano sem grafo nao e engolido pelo
    try que cobre os erros de banco na mesma funcao, que todo no traz x e y
    numericos e que o grafo com no sem posicao falha com mensagem clara.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
    04/11/2026 - Caio - Testes de x/y nos nos e do layout ausente.
"""

from tests import cenario


def test_grafo_do_ano_traz_nos_e_arestas(cliente):
    resposta = cliente.get(f"/anos/{cenario.ANO}/grafo")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ano"] == cenario.ANO
    assert [no["deputado_id"] for no in corpo["nos"]] == cenario.NOS_DO_GRAFO
    arestas = [(a["deputado_a"], a["deputado_b"]) for a in corpo["arestas"]]
    assert arestas == cenario.ARESTAS_DO_GRAFO


def test_toda_aresta_liga_dois_nos_do_grafo(cliente):
    """
    Invariante do grafo: aresta apontando para no que nao esta na lista
    deixaria a tela sem onde desenhar a ponta.
    """
    corpo = cliente.get(f"/anos/{cenario.ANO}/grafo").json()
    ids = {no["deputado_id"] for no in corpo["nos"]}

    for aresta in corpo["arestas"]:
        assert aresta["deputado_a"] in ids
        assert aresta["deputado_b"] in ids


def test_todo_no_traz_x_e_y_numericos(cliente):
    """O front desenha com layout preset: x e y sao obrigatorios e numericos."""
    corpo = cliente.get(f"/anos/{cenario.ANO}/grafo").json()

    for no in corpo["nos"]:
        assert set(no) == {"deputado_id", "nome", "sigla_partido", "sigla_uf", "x", "y"}
        assert isinstance(no["x"], (int, float)) and not isinstance(no["x"], bool)
        assert isinstance(no["y"], (int, float)) and not isinstance(no["y"], bool)


def test_no_traz_a_posicao_gravada_pela_carga(cliente):
    corpo = cliente.get(f"/anos/{cenario.ANO}/grafo").json()
    posicoes = {no["deputado_id"]: (no["x"], no["y"]) for no in corpo["nos"]}

    assert posicoes == cenario.POSICOES


def test_no_sem_posicao_devolve_500_com_mensagem_clara(cliente):
    """
    Em 2022, Alberto esta no grafo mas ficou sem posicao. A rota nao inventa
    0,0 nem esconde o no: falha dizendo o ano e o que fazer.
    """
    resposta = cliente.get(f"/anos/{cenario.ANO_SEM_LAYOUT}/grafo")

    assert resposta.status_code == 500
    detalhe = resposta.json()["detail"]
    assert f"Layout ausente para o ano {cenario.ANO_SEM_LAYOUT}" in detalhe
    assert "rode a carga" in detalhe


def test_ano_sem_grafo_devolve_404(cliente):
    resposta = cliente.get(f"/anos/{cenario.ANO_SEM_EXECUCAO}/grafo")

    assert resposta.status_code == 404
    assert str(cenario.ANO_SEM_EXECUCAO) in resposta.json()["detail"]


def test_ano_com_execucao_mas_sem_concordancia_devolve_grafo_vazio(cliente):
    """2023 tem execucao, entao nao e 404; so nao tem par calculado."""
    resposta = cliente.get(f"/anos/{cenario.ANO_ANTERIOR}/grafo")

    assert resposta.status_code == 200
    assert resposta.json() == {"ano": cenario.ANO_ANTERIOR, "nos": [], "arestas": []}


def test_ano_nao_numerico_devolve_422(cliente):
    assert cliente.get("/anos/abc/grafo").status_code == 422
