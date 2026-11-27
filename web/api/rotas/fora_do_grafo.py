"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/rotas/fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Rota GET /anos/{ano}/fora-do-grafo, com os deputados que votaram no ano
    mas nao entraram no grafo. A interface usa a lista na legenda e na busca.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

import psycopg
from fastapi import APIRouter, HTTPException

from banco import conectar
from servicos.erros import NaoEncontrado
from servicos.fora_do_grafo import obter_fora_do_grafo

router = APIRouter()


@router.get("/anos/{ano}/fora-do-grafo")
def listar_fora_do_grafo_do_ano(ano: int):
    """
    Deputados com voto no ano que ficaram fora do grafo, com quantas
    votacoes contaram para cada um e o motivo. Ano sem grafo devolve 404.
    """
    try:
        with conectar() as conexao:
            return obter_fora_do_grafo(conexao, ano)
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")
