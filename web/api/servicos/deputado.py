"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/servicos/deputado.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Regra de negocio da ficha do deputado: separa o que e 404 (ano sem grafo,
    deputado que nao votou no ano) do que e resposta valida com lista vazia
    (votou, mas ficou fora do grafo por ter poucas votacoes em comum).

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao.
"""

from repositorios.deputado import buscar_ficha, listar_mais_similares
from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.voto import deputados_que_votaram
from servicos.erros import NaoEncontrado


def obter_ficha(conexao, ano, deputado_id, limite):
    """
    Ficha do deputado no ano e os parlamentares com quem ele mais concorda.
    Levanta NaoEncontrado se o ano nao tem grafo ou se ele nao votou no ano.
    Quem votou mas ficou fora do grafo volta com a ficha e a lista vazia.
    """
    execucao_id = buscar_execucao_mais_recente(conexao, ano)
    if execucao_id is None:
        raise NaoEncontrado(f"Nao ha grafo para {ano}")

    # Quem nao votou no ano nao tem ficha a mostrar naquele ano, mesmo que
    # exista na tabela de deputados. Id inexistente cai aqui tambem.
    if not deputados_que_votaram(conexao, ano, [deputado_id]):
        raise NaoEncontrado(f"Deputado sem voto em {ano}: {deputado_id}")

    # Depois do teste acima o deputado existe: app.voto tem chave estrangeira
    # para app.deputado, entao quem votou esta cadastrado.
    ficha = buscar_ficha(conexao, deputado_id)
    similares = listar_mais_similares(conexao, execucao_id, deputado_id, limite)

    return {
        "ano": ano,
        "deputado": ficha,
        "mais_similares": similares,
    }
