"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/rotas/grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Rota GET /anos/{ano}/grafo, que alimenta a tela inicial inteira: o grafo,
    a legenda e as estatisticas saem desta resposta, para os numeros da tela
    baterem entre si.

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao.
"""

import psycopg
from fastapi import APIRouter, HTTPException

from banco import conectar
from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.grafo import listar_nos, listar_arestas

router = APIRouter()


@router.get("/anos/{ano}/grafo")
def obter_grafo(ano: int):
    """
    Grafo de similaridade do ano, sempre da execucao mais recente:
    os deputados que entraram no grafo e as arestas entre eles.
    Ano sem execucao devolve 404.
    """
    try:
        with conectar() as conexao:
            execucao_id = buscar_execucao_mais_recente(conexao, ano)
            if execucao_id is None:
                raise HTTPException(status_code=404, detail=f"Nao ha grafo para {ano}")

            nos = listar_nos(conexao, execucao_id)
            arestas = listar_arestas(conexao, execucao_id)
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")

    return {"ano": ano, "nos": nos, "arestas": arestas}
