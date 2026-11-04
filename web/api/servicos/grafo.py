"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/servicos/grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Regra de negocio do grafo do ano: usa sempre a execucao mais recente e
    exige que todo no tenha posicao x/y. A interface desenha o grafo com as
    posicoes prontas; no sem posicao e erro da carga, e nao se esconde com
    um valor padrao.
"""

from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.grafo import listar_arestas, listar_nos
from servicos.erros import LayoutAusente, NaoEncontrado


def obter_grafo(conexao, ano):
    """
    Nos (com x e y) e arestas do grafo do ano, da execucao mais recente.
    Levanta NaoEncontrado se o ano nao tem execucao e LayoutAusente se algum
    no ficou sem posicao.
    """
    execucao_id = buscar_execucao_mais_recente(conexao, ano)
    if execucao_id is None:
        raise NaoEncontrado(f"Nao ha grafo para {ano}")

    nos = listar_nos(conexao, execucao_id)
    sem_posicao = [no["deputado_id"] for no in nos if no["x"] is None or no["y"] is None]
    if sem_posicao:
        raise LayoutAusente(
            f"Layout ausente para o ano {ano} ({len(sem_posicao)} deputado(s) sem posicao "
            f"na execucao {execucao_id}); rode a carga"
        )

    arestas = listar_arestas(conexao, execucao_id)
    return {"ano": ano, "nos": nos, "arestas": arestas}
