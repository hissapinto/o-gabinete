"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/repositorios/test_voto.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de repositorios/voto.py, onde mora a RN01 do lado da API. Sao os
    testes mais importantes da suite: se a regra daqui divergir da do
    pipeline/similaridade.py, a tela passa a mostrar uma lista que nao bate
    com o percentual exibido ao lado dela, sem nenhum erro aparecer.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

from repositorios.voto import deputados_que_votaram, listar_votacoes_do_par
from tests import cenario


def votacoes(linhas):
    return [linha["votacao_id"] for linha in linhas]


def concordancias_de_ana_e_bruno(conexao, limite=None, offset=0):
    return listar_votacoes_do_par(
        conexao, cenario.ANO, cenario.ANA, cenario.BRUNO, True, limite, offset
    )


def divergencias_de_ana_e_bruno(conexao, limite=None, offset=0):
    return listar_votacoes_do_par(
        conexao, cenario.ANO, cenario.ANA, cenario.BRUNO, False, limite, offset
    )


# --- quem votou ------------------------------------------------------------

def test_reconhece_quem_votou_no_ano(conexao):
    assert deputados_que_votaram(conexao, cenario.ANO, [cenario.ANA]) == {cenario.ANA}


def test_quem_nunca_votou_nao_aparece(conexao):
    assert deputados_que_votaram(conexao, cenario.ANO, [cenario.ELENA]) == set()


def test_filtra_so_quem_votou_entre_os_pedidos(conexao):
    pedidos = [cenario.ANA, cenario.DIEGO, cenario.ELENA]

    assert deputados_que_votaram(conexao, cenario.ANO, pedidos) == {
        cenario.ANA,
        cenario.DIEGO,
    }


def test_voto_de_outro_ano_nao_conta_para_o_ano_pedido(conexao):
    """Elena nao votou nunca; Ana votou em 2023 e em 2024."""
    assert deputados_que_votaram(conexao, cenario.ANO_ANTERIOR, [cenario.ANA]) == {cenario.ANA}
    assert deputados_que_votaram(conexao, cenario.ANO_SEM_EXECUCAO, [cenario.ANA]) == set()


def test_id_inexistente_nao_quebra(conexao):
    assert deputados_que_votaram(conexao, cenario.ANO, [999999]) == set()


# --- a RN01 ----------------------------------------------------------------

def test_concordancias_vem_da_mais_recente_para_a_mais_antiga(conexao):
    assert votacoes(concordancias_de_ana_e_bruno(conexao)) == cenario.ANA_BRUNO_CONCORDARAM


def test_divergencias_vem_da_mais_recente_para_a_mais_antiga(conexao):
    assert votacoes(divergencias_de_ana_e_bruno(conexao)) == cenario.ANA_BRUNO_DIVERGIRAM


def test_obstrucao_conta_como_voto_contra(conexao):
    """
    Em v3 Ana votou Nao e Bruno Obstrucao. Pela RN01 os dois votaram contra,
    entao e concordancia, apesar de os votos estarem escritos diferente.
    """
    linhas = {linha["votacao_id"]: linha for linha in concordancias_de_ana_e_bruno(conexao)}

    assert "v3" in linhas
    assert linhas["v3"]["voto_a"] == "Não"
    assert linhas["v3"]["voto_b"] == "Obstrução"
    assert linhas["v3"]["concordaram"] is True


def test_abstencao_e_artigo_17_ficam_fora_da_conta(conexao):
    todas = votacoes(concordancias_de_ana_e_bruno(conexao)) + votacoes(
        divergencias_de_ana_e_bruno(conexao)
    )

    assert "v6" not in todas, "v6 tem Abstencao e nao deveria entrar"
    assert "v7" not in todas, "v7 tem Artigo 17 e nao deveria entrar"


def test_votacao_de_outro_ano_fica_fora(conexao):
    todas = votacoes(concordancias_de_ana_e_bruno(conexao)) + votacoes(
        divergencias_de_ana_e_bruno(conexao)
    )

    assert "v8" not in todas


def test_as_duas_listas_somam_as_votacoes_em_comum(conexao):
    """
    A soma das duas listas tem de dar o votacoes_em_comum que o pipeline
    gravou. E a verificacao que prova que as duas regras concordam: a da API,
    nesta consulta, e a do pipeline, que gerou o contador.
    """
    em_comum, _, _ = cenario.PARES[(cenario.ANA, cenario.BRUNO)]

    total = len(concordancias_de_ana_e_bruno(conexao)) + len(
        divergencias_de_ana_e_bruno(conexao)
    )

    assert total == em_comum


def test_concordaram_marca_cada_lado_corretamente(conexao):
    assert all(linha["concordaram"] for linha in concordancias_de_ana_e_bruno(conexao))
    assert not any(linha["concordaram"] for linha in divergencias_de_ana_e_bruno(conexao))


def test_ordem_dos_votos_acompanha_a_ordem_dos_ids(conexao):
    """voto_a e o voto do primeiro id pedido, voto_b o do segundo."""
    linhas = {
        linha["votacao_id"]: linha
        for linha in listar_votacoes_do_par(
            conexao, cenario.ANO, cenario.ANA, cenario.BRUNO, False, None, 0
        )
    }

    assert linhas["v4"]["voto_a"] == "Sim"
    assert linhas["v4"]["voto_b"] == "Não"


# --- paginacao -------------------------------------------------------------

def test_sem_limite_traz_a_lista_inteira(conexao):
    _, concordancias, _ = cenario.PARES[(cenario.ANA, cenario.BRUNO)]

    assert len(concordancias_de_ana_e_bruno(conexao, limite=None)) == concordancias


def test_limite_corta_a_lista(conexao):
    assert votacoes(concordancias_de_ana_e_bruno(conexao, limite=2)) == ["v3", "v2"]


def test_offset_avanca_na_lista(conexao):
    assert votacoes(concordancias_de_ana_e_bruno(conexao, limite=2, offset=2)) == ["v1"]


def test_offset_nulo_vale_como_zero(conexao):
    """No PostgreSQL, OFFSET NULL equivale a OFFSET 0."""
    assert votacoes(concordancias_de_ana_e_bruno(conexao, limite=1, offset=None)) == ["v3"]


def test_par_sem_votacao_em_comum_devolve_lista_vazia(conexao):
    """Elena nunca votou, entao nao ha o que listar com ninguem."""
    assert listar_votacoes_do_par(
        conexao, cenario.ANO, cenario.ANA, cenario.ELENA, True, None, 0
    ) == []
