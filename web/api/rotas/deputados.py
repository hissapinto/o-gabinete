"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/rotas/deputados.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Rota GET /anos/{ano}/deputados/{deputado_id}, que abre a ficha quando o
    usuario clica num no do grafo ou acha o deputado pela busca.

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao.
"""

import psycopg
from fastapi import APIRouter, HTTPException, Query

from banco import conectar
from servicos.deputado import obter_ficha
from servicos.erros import NaoEncontrado

router = APIRouter()


@router.get("/anos/{ano}/deputados/{deputado_id}")
def obter_deputado(
    ano: int,
    deputado_id: int,
    limite: int = Query(10, ge=1, le=50),
):
    """
    Ficha do deputado no ano e a lista dos mais similares a ele.
    Ano sem grafo ou deputado que nao votou no ano devolvem 404.
    Quem votou mas ficou fora do grafo devolve 200 com a lista vazia.
    """
    try:
        with conectar() as conexao:
            resultado = obter_ficha(conexao, ano, deputado_id, limite)
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")

    return resultado
