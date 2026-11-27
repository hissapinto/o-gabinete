"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/servicos/fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Regra de negocio da lista de deputados fora do grafo. Quem votou no ano
    mas nao tem nenhum par com o minimo de votacoes em comum nao vira vertice;
    a interface mostra essa lista na legenda e na busca, para o deputado nao
    "sumir" sem explicacao (ideia da Isabela).

    Cada um recebe um motivo:
        "presidencia"      - presidiu a maior parte das sessoes em que esteve
                             (votou "Artigo 17", que fica fora da conta);
        "poucas_votacoes"  - qualquer outro caso: votou pouco no ano, por
                             licenca, suplencia, cargo no Executivo ou faltas.
    Licenca e suplencia nao estao no banco; a interface fala em poucas
    votacoes, sem afirmar a causa.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.fora_do_grafo import (buscar_minimo_em_comum, contar_votacoes_do_ano,
                                        listar_fora_do_grafo)
from servicos.erros import NaoEncontrado


def motivo(votacoes, artigo_17):
    """'presidencia' quando presidiu mais sessoes do que votou; senao 'poucas_votacoes'."""
    return "presidencia" if artigo_17 > votacoes else "poucas_votacoes"


def obter_fora_do_grafo(conexao, ano):
    """
    Deputados que votaram no ano e ficaram fora do grafo da execucao mais
    recente, com o motivo de cada um. Levanta NaoEncontrado se o ano nao tem
    execucao.
    """
    execucao_id = buscar_execucao_mais_recente(conexao, ano)
    if execucao_id is None:
        raise NaoEncontrado(f"Nao ha grafo para {ano}")

    deputados = [
        {**linha, "motivo": motivo(linha["votacoes"], linha["artigo_17"])}
        for linha in listar_fora_do_grafo(conexao, execucao_id, ano)
    ]
    return {
        "ano": ano,
        "total_votacoes": contar_votacoes_do_ano(conexao, ano),
        "minimo_em_comum": buscar_minimo_em_comum(conexao, execucao_id),
        "deputados": deputados,
    }
