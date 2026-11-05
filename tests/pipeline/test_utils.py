"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_utils.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da localizacao da raiz do projeto. O pipeline inteiro depende dela:
    todos os modulos fazem "from utils import RAIZ", e o RAIZ e calculado no
    momento do import, nao na chamada. Um erro aqui nao quebra uma funcao,
    quebra o import de tudo.

    O teste do caso sem marcador so pode existir porque o laco agora tem
    saida. Enquanto ele era infinito, um teste desse caso travaria a suite --
    e na integracao continua um travamento e pior que uma falha, porque o job
    fica rodando ate o tempo limite em vez de dar vermelho em segundos.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

from pathlib import Path

import pytest

from utils import RAIZ, encontrar_raiz


def test_acha_a_raiz_a_partir_da_propria_raiz(monkeypatch, tmp_path):
    (tmp_path / "requirements.txt").touch()
    monkeypatch.chdir(tmp_path)

    assert encontrar_raiz() == tmp_path


def test_sobe_diretorios_ate_achar(monkeypatch, tmp_path):
    """E o caso do container: WORKDIR /app/pipeline, marcador em /app."""
    (tmp_path / "requirements.txt").touch()
    subpasta = tmp_path / "pipeline"
    subpasta.mkdir()
    monkeypatch.chdir(subpasta)

    assert encontrar_raiz() == tmp_path


def test_para_no_primeiro_marcador_encontrado(monkeypatch, tmp_path):
    """Achando mais de um subindo, vale o mais proximo."""
    (tmp_path / "requirements.txt").touch()
    meio = tmp_path / "meio"
    meio.mkdir()
    (meio / "requirements.txt").touch()
    fundo = meio / "fundo"
    fundo.mkdir()
    monkeypatch.chdir(fundo)

    assert encontrar_raiz() == meio


def test_aceita_outro_marcador(monkeypatch, tmp_path):
    (tmp_path / "pyproject.toml").touch()
    monkeypatch.chdir(tmp_path)

    assert encontrar_raiz("pyproject.toml") == tmp_path


def test_erro_claro_quando_nao_existe_marcador_acima(monkeypatch, tmp_path):
    """
    Sem o marcador em lugar nenhum acima, a funcao tem de parar na raiz do
    sistema e dizer o que houve. Antes da correcao, este teste nunca
    terminaria.
    """
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="marcador_que_nao_existe"):
        encontrar_raiz("marcador_que_nao_existe.txt")


def test_mensagem_de_erro_diz_de_onde_a_busca_partiu(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError) as erro:
        encontrar_raiz("marcador_que_nao_existe.txt")

    assert "Rode o pipeline de dentro do projeto" in str(erro.value)


def test_raiz_do_modulo_aponta_para_o_projeto():
    """O RAIZ calculado no import tem de conter o requirements.txt."""
    assert (RAIZ / "requirements.txt").exists()
    assert isinstance(RAIZ, Path)
