"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/rotas/anos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Rota GET /anos, que preenche o seletor de ano da tela inicial.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao.
"""

import psycopg
from fastapi import APIRouter, HTTPException

from banco import conectar
from repositorios.execucao import listar_anos_disponiveis

router = APIRouter()


@router.get("/anos")
def listar_anos():
    """Anos com grafo disponivel, do mais recente ao mais antigo."""
    try:
        with conectar() as conexao:
            anos = listar_anos_disponiveis(conexao)
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")

    return {"anos": anos}
