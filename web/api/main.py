"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/main.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    API em FastAPI que liga a interface ao banco PostgreSQL. Cria a aplicacao,
    registra os routers de cada recurso e mantem as rotas /health e
    /deputados do Hello World.

Historico de alteracoes:
    25/09/2026 - Caio - Criacao do Hello World atravessando as tres camadas.
    17/10/2026 - Caio - Conexao movida para banco.py e inclusao do router /anos.
"""

import psycopg
from fastapi import FastAPI, HTTPException

from banco import conectar
from rotas.anos import router as anos_router

app = FastAPI(title="O Gabinete - API")
app.include_router(anos_router)


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
