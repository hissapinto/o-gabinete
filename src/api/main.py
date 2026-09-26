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
