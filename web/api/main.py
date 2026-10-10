"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/api/main.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    API em FastAPI que liga a interface ao banco PostgreSQL. Expoe a rota
    /health, que confirma que o servico esta no ar, e a rota /deputados,
    que lista os deputados cadastrados na camada de dados.

Historico de alteracoes:
    25/09/2026 - Caio - Criacao do Hello World atravessando as tres camadas.
"""

import os

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row

app = FastAPI(title="O Gabinete - API")

DATABASE_URL = os.environ["DATABASE_URL"]

def conectar():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

@app.get("/health")
def health():
    """Confirma que a API esta no ar, sem tocar no banco."""
    return {"status": "ok", "servico": "backend"}

@app.get("/deputados")
def listar_deputados():
    """Devolve os deputados cadastrados na camada de dados."""
    try:
        with conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT deputado_id, nome, sigla_partido, sigla_uf, url_foto
                    FROM app.deputado
                    ORDER BY nome
                    """
                )
                return cursor.fetchall()
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")