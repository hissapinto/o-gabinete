"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/servicos/test_deputado.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de servicos/deputado.py. A camada tem tres desfechos possiveis, e
    o que importa aqui e que cada entrada caia no desfecho certo: ano sem
    grafo e deputado sem voto levantam NaoEncontrado; quem votou mas ficou
    fora do grafo volta com a ficha e a lista vazia.

    Testa tambem a ordem dos dois testes dentro do servico: um deputado
    cadastrado que nao votou no ano precisa levantar NaoEncontrado, e nao
    voltar com ficha.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

import pytest

from servicos.deputado import obter_ficha
from servicos.erros import NaoEncontrado
from tests import cenario


def test_ficha_do_deputado_no_grafo(conexao):
    resultado = obter_ficha(conexao, cenario.ANO, cenario.ANA, 10)

    assert resultado["ano"] == cenario.ANO
    assert resultado["deputado"]["deputado_id"] == cenario.ANA
    assert resultado["deputado"]["nome"] == cenario.NOMES[cenario.ANA]
    assert [s["deputado_id"] for s in resultado["mais_similares"]] == cenario.SIMILARES_DE_ANA


def test_resposta_tem_sempre_as_mesmas_chaves(conexao):
    no_grafo = obter_ficha(conexao, cenario.ANO, cenario.ANA, 10)
    fora_do_grafo = obter_ficha(conexao, cenario.ANO, cenario.DIEGO, 10)

    assert set(no_grafo) == set(fora_do_grafo) == {"ano", "deputado", "mais_similares"}


def test_quem_votou_mas_ficou_fora_do_grafo_volta_com_lista_vazia(conexao):
    """
    E o desfecho mais facil de errar: a tentacao e tratar como 404, mas o
    deputado existe e votou, so nao tem par calculado. A tela precisa da
    ficha dele para poder dizer isso ao usuario.
    """
    resultado = obter_ficha(conexao, cenario.ANO, cenario.DIEGO, 10)

    assert resultado["deputado"]["deputado_id"] == cenario.DIEGO
    assert resultado["mais_similares"] == []


def test_ano_sem_grafo_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado, match=str(cenario.ANO_SEM_EXECUCAO)):
        obter_ficha(conexao, cenario.ANO_SEM_EXECUCAO, cenario.ANA, 10)


def test_deputado_cadastrado_que_nao_votou_levanta_nao_encontrado(conexao):
    """
    Elena existe em app.deputado. Se o servico buscasse a ficha antes de
    verificar os votos, este caso voltaria 200 com lista vazia, que e o
    desfecho de Diego, e os dois significam coisas diferentes.
    """
    with pytest.raises(NaoEncontrado, match=str(cenario.ELENA)):
        obter_ficha(conexao, cenario.ANO, cenario.ELENA, 10)


def test_id_inexistente_levanta_nao_encontrado(conexao):
    with pytest.raises(NaoEncontrado):
        obter_ficha(conexao, cenario.ANO, 999999, 10)


def test_limite_e_repassado_para_a_consulta(conexao):
    resultado = obter_ficha(conexao, cenario.ANO, cenario.ANA, 1)

    assert len(resultado["mais_similares"]) == 1


def test_usa_a_execucao_mais_recente_do_ano(conexao):
    """
    Na execucao antiga Ana so tem par com Bruno, a 100.00. Na atual tem
    quatro pares. Se o servico pegasse a execucao errada, a lista teria um
    item so.
    """
    resultado = obter_ficha(conexao, cenario.ANO, cenario.ANA, 10)

    assert len(resultado["mais_similares"]) == len(cenario.SIMILARES_DE_ANA)
    assert str(resultado["mais_similares"][-1]["percentual"]) == "60.00"
