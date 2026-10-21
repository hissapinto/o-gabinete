"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/conftest.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Preparacao compartilhada da suite. Cria um banco separado so para os
    testes, aplica nele o mesmo infra/db/init/01-schema.sql que o container
    usa, grava o cenario de tests/cenario.py e entrega as duas portas de
    entrada que os testes usam: uma conexao, para as camadas de repositorio e
    servico, e um cliente HTTP, para a camada de rotas.

    O banco e separado de proposito: a suite apaga e recria o banco de teste
    a cada execucao, e nunca toca no banco de desenvolvimento.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

import os
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

from tests.cenario import SQL as SQL_DO_CENARIO

# A raiz do repositorio, a partir deste arquivo:
# tests -> api -> web -> raiz
RAIZ = Path(__file__).resolve().parents[3]
ESQUEMA = RAIZ / "infra" / "db" / "init" / "01-schema.sql"

HOST = os.environ.get("POSTGRES_HOST", "localhost")
PORTA = os.environ.get("POSTGRES_PORT", "5432")
USUARIO = os.environ.get("POSTGRES_USER", "gabinete")
SENHA = os.environ.get("POSTGRES_PASSWORD", "gabinete_local")
BANCO_DE_TESTE = os.environ.get("POSTGRES_DB_TESTE", "gabinete_teste")

# O banco de manutencao, usado apenas para apagar e criar o de teste.
BANCO_DE_SERVICO = os.environ.get("POSTGRES_DB", "postgres")


def _url(banco):
    return f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{banco}"


@pytest.fixture(scope="session")
def url_do_banco():
    """
    Recria o banco de teste, aplica o esquema real e grava o cenario.

    Interrompe a suite com instrucao em vez de deixar todos os testes
    falharem quando o banco nao esta no ar: a causa mais comum e simples de
    corrigir, e um erro por teste esconderia a mensagem util.
    """
    if not ESQUEMA.exists():
        pytest.exit(f"Esquema nao encontrado em {ESQUEMA}", returncode=1)

    try:
        with psycopg.connect(_url(BANCO_DE_SERVICO), autocommit=True) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(f'DROP DATABASE IF EXISTS "{BANCO_DE_TESTE}" WITH (FORCE)')
                cursor.execute(f'CREATE DATABASE "{BANCO_DE_TESTE}"')
    except psycopg.OperationalError as erro:
        pytest.exit(
            "Nao foi possivel falar com o PostgreSQL em "
            f"{HOST}:{PORTA} como {USUARIO}.\n"
            "Suba os containers com 'docker compose up -d' e tente de novo.\n"
            f"Erro do driver: {erro}",
            returncode=1,
        )

    url = _url(BANCO_DE_TESTE)
    with psycopg.connect(url, autocommit=True) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(ESQUEMA.read_text(encoding="utf-8"))
            cursor.execute(SQL_DO_CENARIO)

    return url


@pytest.fixture
def conexao(url_do_banco):
    """
    Conexao com o banco de teste, com as linhas vindo como dicionario, igual
    ao que banco.conectar() entrega em producao.

    Usada pelos testes de repositorio e de servico, que recebem a conexao de
    quem os chama em vez de abrir a propria.
    """
    with psycopg.connect(url_do_banco, row_factory=dict_row) as conexao:
        yield conexao


@pytest.fixture(scope="session")
def cliente(url_do_banco):
    """
    Cliente HTTP sobre a aplicacao, para os testes de rota.

    main.py importa banco.py, que le DATABASE_URL no momento da importacao.
    Por isso a variavel e definida aqui antes do import, que fica dentro da
    funcao de proposito: importado no topo do arquivo, o modulo leria a
    DATABASE_URL de desenvolvimento.
    """
    os.environ["DATABASE_URL"] = url_do_banco

    from fastapi.testclient import TestClient

    import main

    return TestClient(main.app)
