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

    CORS so liga quando CORS_ORIGINS traz origens (separadas por virgula).
    No compose e no Render o front chega pela mesma origem (proxy /api/ e
    rewrite), entao o padrao e vazio, sem CORS.

Historico de alteracoes:
      25/09/2026 - Caio - Criacao do Hello World atravessando as tres camadas.
      17/10/2026 - Caio - Conexao movida para banco.py e inclusao do router /anos.
      17/10/2026 - Caio - Inclusao do router de concordancias.
      19/10/2026 - Isabela - Inclusao do router do grafo.
      19/10/2026 - Isabela - Inclusao do router de deputados.
      04/11/2026 - Caio - CORS configuravel por CORS_ORIGINS, para o deploy.
"""

import os

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from banco import conectar
from rotas.anos import router as anos_router
from rotas.concordancias import router as concordancias_router
from rotas.deputados import router as deputados_router
from rotas.grafo import router as grafo_router

app = FastAPI(title="O Gabinete - API")


def origens_cors(valor):
    """'https://a.com, https://b.com' -> ['https://a.com', 'https://b.com']."""
    return [origem.strip().rstrip("/") for origem in valor.split(",") if origem.strip()]


ORIGENS_CORS = origens_cors(os.environ.get("CORS_ORIGINS", ""))
if ORIGENS_CORS:
    # A API so tem GET, e a interface nao manda cookie nem credencial.
    app.add_middleware(CORSMiddleware, allow_origins=ORIGENS_CORS, allow_methods=["GET"])

app.include_router(anos_router)
app.include_router(concordancias_router)
app.include_router(grafo_router)
app.include_router(deputados_router)

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
