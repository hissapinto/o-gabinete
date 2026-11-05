"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_coleta.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da configuracao da coleta. O ANO_REFERENCIA e o unico ponto do
    pipeline que fixa o ano: dele saem os quatro enderecos da Camara, os nomes
    dos CSVs intermediarios e a execucao gravada no banco.

    O teste mais importante e o de coerencia dos enderecos. Se alguem fixar o
    ano em um deles e esquecer os outros, o pipeline baixaria arquivos de anos
    diferentes e cruzaria os votos de um ano com as votacoes de outro -- sem
    erro nenhum aparecer, so numeros errados no grafo.

    Nao se testa o download em si: ele depende da rede e do Portal da Camara,
    e um teste assim falharia por indisponibilidade de terceiros.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao, junto da configuracao do ano por ambiente.
"""

import importlib

import pytest

import coleta


URLS = ("URL_VOTOS", "URL_VOTACOES", "URL_OBJETOS", "URL_PROPOSICOES")


def test_os_quatro_enderecos_usam_o_mesmo_ano():
    ano = str(coleta.ANO_REFERENCIA)

    for nome in URLS:
        endereco = getattr(coleta, nome)
        assert f"-{ano}.csv" in endereco, f"{nome} nao aponta para {ano}"


def test_enderecos_sao_do_portal_da_camara():
    for nome in URLS:
        assert getattr(coleta, nome).startswith("https://dadosabertos.camara.leg.br/")


def test_ano_padrao_quando_o_ambiente_nao_define(monkeypatch):
    """Sem a variavel, o pipeline continua carregando 2024, como antes."""
    monkeypatch.delenv("ANO_REFERENCIA", raising=False)
    recarregado = importlib.reload(coleta)
    try:
        assert recarregado.ANO_REFERENCIA == 2024
    finally:
        importlib.reload(coleta)


def test_ano_vem_do_ambiente(monkeypatch):
    """E o que permite carregar os outros anos da legislatura sem tocar no codigo."""
    monkeypatch.setenv("ANO_REFERENCIA", "2023")
    recarregado = importlib.reload(coleta)
    try:
        assert recarregado.ANO_REFERENCIA == 2023
        for nome in URLS:
            assert "-2023.csv" in getattr(recarregado, nome)
    finally:
        monkeypatch.delenv("ANO_REFERENCIA", raising=False)
        importlib.reload(coleta)


def test_ano_e_inteiro():
    """A variavel de ambiente chega como texto; o resto do pipeline espera int."""
    assert isinstance(coleta.ANO_REFERENCIA, int)


def test_parametros_do_download_sao_coerentes():
    assert coleta.TENTATIVAS > coleta.PARADAS_ACEITAS, (
        "desistir por falta de progresso tem de vir antes de esgotar as tentativas"
    )
    assert coleta.PEDACO > 0
    assert coleta.TEMPO_LIMITE > 0


def test_timeout_de_rede_vira_mais_uma_tentativa(monkeypatch, tmp_path):
    """
    requests.RequestException herda de OSError, mas um TimeoutError cru nao e
    RequestException. Capturando so RequestException, um timeout escapava do
    laco de tentativas e derrubava a carga inteira -- foi o que aconteceu ao
    baixar 2026. Agora ele e tratado como as demais falhas de rede, e a
    desistencia vem do guarda de progresso, com mensagem.
    """
    monkeypatch.setattr(coleta, "ESPERA", 0)
    monkeypatch.setattr(coleta, "tamanho_no_servidor", lambda url: 1000)
    monkeypatch.setattr(
        coleta, "continuar_download",
        lambda url, parcial, inicio: (_ for _ in ()).throw(TimeoutError(60, "Operation timed out")),
    )

    with pytest.raises(RuntimeError, match="download parado"):
        coleta.baixar("https://exemplo.test/votacoesVotos-2026.csv", tmp_path / "arquivo.csv")


def test_falha_de_rede_comum_tambem_vira_tentativa(monkeypatch, tmp_path):
    """O caminho que ja funcionava antes continua funcionando."""
    import requests

    monkeypatch.setattr(coleta, "ESPERA", 0)
    monkeypatch.setattr(coleta, "tamanho_no_servidor", lambda url: 1000)
    monkeypatch.setattr(
        coleta, "continuar_download",
        lambda url, parcial, inicio: (_ for _ in ()).throw(requests.ConnectionError("caiu")),
    )

    with pytest.raises(RuntimeError, match="download parado"):
        coleta.baixar("https://exemplo.test/arquivo.csv", tmp_path / "arquivo.csv")
