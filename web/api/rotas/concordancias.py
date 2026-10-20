"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/rotas/concordancias.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Rota GET /anos/{ano}/concordancias/{deputado_a}/{deputado_b}, que mostra
    por que dois deputados se parecem: usada no clique na aresta e no clique
    num item da lista de mais similares.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao.
    19/10/2026 - Isabela - Inclusao do parametro tipo e separacao das votacoes
                           em duas listas, concordancias e divergencias.
    19/10/2026 - Isabela - limite passou a ser opcional: sem limite, a
                           resposta traz as listas inteiras.
"""

from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query

from banco import conectar
from servicos.concordancia import obter_concordancia
from servicos.erros import NaoEncontrado

router = APIRouter()


@router.get("/anos/{ano}/concordancias/{deputado_a}/{deputado_b}")
def obter_concordancia_do_par(
    ano: int,
    deputado_a: int,
    deputado_b: int,
    tipo: Literal["todas", "concordancia", "divergencia"] = "todas",
    limite: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    """
    Concordancia entre dois deputados no ano e as votacoes em comum, em duas
    listas: as em que concordaram e as em que divergiram.

    tipo escolhe quais listas vem preenchidas; a outra vem nula.
    limite pagina cada lista; sem limite, cada lista vem inteira.
    A ordem dos ids nao importa. Par com poucas votacoes em comum volta com
    status "insuficiente".
    """
    if deputado_a == deputado_b:
        raise HTTPException(status_code=422, detail="Informe dois deputados diferentes")

    try:
        with conectar() as conexao:
            resultado = obter_concordancia(
                conexao, ano, deputado_a, deputado_b, tipo, limite, offset
            )
    except NaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except psycopg.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")

    return resultado
