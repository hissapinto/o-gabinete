"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/servicos/concordancia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Regra de negocio da concordancia entre dois deputados: normaliza a ordem
    do par, decide entre nao encontrado, dados insuficientes e dados
    completos, e monta a resposta, sempre com as mesmas chaves.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao.
"""

from repositorios.concordancia import buscar_concordancia
from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.voto import deputados_que_votaram, listar_divergencias
from servicos.erros import NaoEncontrado


def obter_concordancia(conexao, ano, deputado_a, deputado_b, limite, offset):
    """
    Concordancia do par no ano, com uma pagina das votacoes em que divergiram.
    Levanta NaoEncontrado se o ano nao tem grafo ou se algum dos dois nao
    votou no ano. Par sem votacoes em comum suficientes -> status "insuficiente".
    """
    # o banco guarda cada par uma vez, sempre com o menor id em deputado_a
    deputado_a, deputado_b = min(deputado_a, deputado_b), max(deputado_a, deputado_b)

    execucao_id = buscar_execucao_mais_recente(conexao, ano)
    if execucao_id is None:
        raise NaoEncontrado(f"Nao ha grafo para {ano}")

    pedidos = {deputado_a, deputado_b}
    faltando = pedidos - deputados_que_votaram(conexao, ano, pedidos)
    if faltando:
        ids = ", ".join(str(i) for i in sorted(faltando))
        raise NaoEncontrado(f"Deputado(s) sem voto em {ano}: {ids}")

    par = buscar_concordancia(conexao, execucao_id, deputado_a, deputado_b)
    if par is None:
        return _montar_resposta(ano, deputado_a, deputado_b, "insuficiente",
                                None, None, None, None, [], 0, limite, offset)

    divergencias = par["votacoes_em_comum"] - par["concordancias"]
    itens = listar_divergencias(conexao, ano, deputado_a, deputado_b, limite, offset)
    return _montar_resposta(ano, deputado_a, deputado_b, "completo",
                            par["votacoes_em_comum"], par["concordancias"], divergencias,
                            par["percentual"], itens, divergencias, limite, offset)


def _montar_resposta(ano, deputado_a, deputado_b, status, votacoes_em_comum,
                     concordancias, divergencias, percentual, itens, total, limite, offset):
    """Unico lugar que monta a resposta: os dois casos saem com as mesmas chaves."""
    return {
        "ano": ano,
        "deputado_a": deputado_a,
        "deputado_b": deputado_b,
        "status": status,
        "votacoes_em_comum": votacoes_em_comum,
        "concordancias": concordancias,
        "divergencias": divergencias,
        "percentual": percentual,
        "lista_divergencias": {
            "itens": itens,
            "total": total,
            "limite": limite,
            "offset": offset,
        },
    }
