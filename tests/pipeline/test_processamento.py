"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_processamento.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes do filtro de votacoes de merito, que decide quais votacoes entram
    na conta de concordancia. Um filtro frouxo demais deixa entrar
    requerimento e adiamento, que dizem pouco sobre posicao politica; um
    filtro apertado demais joga fora votacao que importa. Nos dois casos o
    grafo inteiro muda, sem erro nenhum aparecer.

    Nao sao testadas processar_votos e filtrar_votos_merito: as duas gravam
    arquivos em dados/processado/ do repositorio, e um teste nao deve escrever
    fora da pasta temporaria.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

import pandas as pd
import pytest

from processamento import (
    PADRAO_PROCEDIMENTAL,
    TIPOS_DE_MERITO,
    ler_csv_camara,
    votacoes_de_merito,
)
from coleta import ANO_REFERENCIA


def escrever_csv(pasta, nome, linhas, colunas):
    caminho = pasta / nome
    pd.DataFrame(linhas, columns=colunas).to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    return caminho


@pytest.fixture
def brutos(tmp_path):
    """
    Monta os dois CSVs que votacoes_de_merito le, cobrindo os tres motivos de
    exclusao: tipo que nao e de merito, orgao que nao e o Plenario, e descricao
    procedimental.
    """
    escrever_csv(tmp_path, f"votacoesProposicoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PL"),      # merito
        ("vB", "PEC"),     # merito
        ("vC", "REQ"),     # tipo fora da lista
        ("vD", "PL"),      # merito, mas de comissao
        ("vE", "MPV"),     # merito, mas procedimental
        ("vF", "PLP"),     # merito
    ], ["idVotacao", "proposicao_siglaTipo"])

    escrever_csv(tmp_path, f"votacoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PLEN", "Aprovacao do texto-base"),
        ("vB", "PLEN", "Votacao em primeiro turno"),
        ("vC", "PLEN", "Requerimento de urgencia"),
        ("vD", "CCJC", "Aprovacao do parecer"),
        ("vE", "PLEN", "Requerimento de adiamento da discussao"),
        ("vF", "PLEN", "Aprovacao da redacao final"),
    ], ["id", "siglaOrgao", "descricao"])

    return tmp_path


def test_seleciona_apenas_as_votacoes_de_merito(brutos):
    assert sorted(votacoes_de_merito(brutos)) == ["vA", "vB", "vF"]


def test_descarta_tipo_que_nao_e_proposicao_legislativa(brutos):
    assert "vC" not in votacoes_de_merito(brutos)


def test_descarta_votacao_fora_do_plenario(brutos):
    assert "vD" not in votacoes_de_merito(brutos)


def test_descarta_votacao_procedimental(brutos):
    """Adiamento e sobre o andamento da pauta, nao sobre o conteudo."""
    assert "vE" not in votacoes_de_merito(brutos)


def test_nao_repete_id_de_votacao(tmp_path):
    """Uma votacao pode afetar mais de uma proposicao, e apareceria duas vezes."""
    escrever_csv(tmp_path, f"votacoesProposicoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PL"), ("vA", "PEC"),
    ], ["idVotacao", "proposicao_siglaTipo"])
    escrever_csv(tmp_path, f"votacoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PLEN", "Aprovacao do texto-base"),
    ], ["id", "siglaOrgao", "descricao"])

    assert list(votacoes_de_merito(tmp_path)) == ["vA"]


def test_descricao_vazia_nao_quebra(tmp_path):
    escrever_csv(tmp_path, f"votacoesProposicoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PL"),
    ], ["idVotacao", "proposicao_siglaTipo"])
    escrever_csv(tmp_path, f"votacoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PLEN", None),
    ], ["id", "siglaOrgao", "descricao"])

    assert list(votacoes_de_merito(tmp_path)) == ["vA"]


def test_padrao_procedimental_ignora_maiusculas(tmp_path):
    escrever_csv(tmp_path, f"votacoesProposicoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PL"),
    ], ["idVotacao", "proposicao_siglaTipo"])
    escrever_csv(tmp_path, f"votacoes-{ANO_REFERENCIA}.csv", [
        ("vA", "PLEN", "REQUERIMENTO DE URGENCIA"),
    ], ["id", "siglaOrgao", "descricao"])

    assert list(votacoes_de_merito(tmp_path)) == []


def test_lista_de_tipos_cobre_as_proposicoes_legislativas():
    for sigla in ("PL", "PEC", "MPV", "PLP"):
        assert sigla in TIPOS_DE_MERITO


def test_padrao_procedimental_cobre_os_casos_conhecidos():
    for termo in ("requerimento", "adiamento", "encerramento"):
        assert termo in PADRAO_PROCEDIMENTAL


def test_le_csv_da_camara_com_ponto_e_virgula(tmp_path):
    """Os arquivos da Camara usam ponto e virgula e BOM."""
    caminho = escrever_csv(tmp_path, "amostra.csv", [("a", 1)], ["coluna", "valor"])

    df = ler_csv_camara(caminho)

    assert list(df.columns) == ["coluna", "valor"]
    assert df.iloc[0]["coluna"] == "a"
