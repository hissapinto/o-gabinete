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
    baterem entre si. Cada no traz x e y, o layout calculado pelo pipeline.

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao.
    04/11/2026 - Caio - Regra movida para servicos/grafo.py; nos com x e y,
                        e 500 quando falta o layout.
"""

import psycopg
from fastapi import APIRouter, HTTPException

from banco import conectar
from servicos.erros import LayoutAusente, NaoEncontrado
from servicos.grafo import obter_grafo

router = APIRouter()


@router.get("/anos/{ano}/grafo")
def obter_grafo_do_ano(ano: int):
    """
    Grafo de similaridade do ano, sempre da execucao mais recente:
    os deputados que entraram no grafo, com a posicao x/y de cada um no
    desenho, e as arestas entre eles.
    Ano sem execucao devolve 404. No sem posicao devolve 500, porque e falha
    da carga e nao do pedido.
    """
    try:
        with conectar() as conexao:
            return obter_grafo(conexao, ano)
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except LayoutAusente as erro:
        raise HTTPException(status_code=500, detail=str(erro))
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")
