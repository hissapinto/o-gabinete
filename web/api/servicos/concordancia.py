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
    19/10/2026 - Isabela - A lista unica de divergencias virou duas listas,
                           concordancias e divergencias, cada uma com o seu
                           total, para atender o wireframe 4.3.
    19/10/2026 - Isabela - limite opcional: None traz as listas inteiras.
"""

from repositorios.concordancia import buscar_concordancia
from repositorios.execucao import buscar_execucao_mais_recente
from repositorios.voto import deputados_que_votaram, listar_votacoes_do_par
from servicos.erros import NaoEncontrado


def obter_concordancia(conexao, ano, deputado_a, deputado_b, tipo, limite, offset):
    """
    Concordancia do par no ano e as votacoes em comum, em duas listas: as em
    que os dois concordaram e as em que divergiram. O tipo escolhe quais
    listas vem preenchidas; a que nao foi pedida vem como None, que se
    distingue de uma lista vazia de verdade.

    Levanta NaoEncontrado se o ano nao tem grafo ou se algum dos dois nao
    votou no ano. Par sem votacoes em comum suficientes -> status
    "insuficiente", que e o campo que a tela deve consultar antes das listas.
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
        return _montar_resposta(
            ano, deputado_a, deputado_b, "insuficiente",
            None, None, None, None, tipo,
            _lista_vazia(tipo, "concordancia"), _lista_vazia(tipo, "divergencia"),
            limite, offset,
        )

    divergencias = par["votacoes_em_comum"] - par["concordancias"]

    lista_concordancias = None
    if tipo in ("todas", "concordancia"):
        lista_concordancias = {
            "itens": listar_votacoes_do_par(
                conexao, ano, deputado_a, deputado_b, True, limite, offset),
            "total": par["concordancias"],
        }

    lista_divergencias = None
    if tipo in ("todas", "divergencia"):
        lista_divergencias = {
            "itens": listar_votacoes_do_par(
                conexao, ano, deputado_a, deputado_b, False, limite, offset),
            "total": divergencias,
        }

    return _montar_resposta(
        ano, deputado_a, deputado_b, "completo",
        par["votacoes_em_comum"], par["concordancias"], divergencias,
        par["percentual"], tipo,
        lista_concordancias, lista_divergencias,
        limite, offset,
    )


def _lista_vazia(tipo, lado):
    """Bloco vazio para o par sem dados, so nos lados que foram pedidos."""
    if tipo in ("todas", lado):
        return {"itens": [], "total": 0}
    return None


def _montar_resposta(ano, deputado_a, deputado_b, status, votacoes_em_comum,
                     concordancias, divergencias, percentual, tipo,
                     lista_concordancias, lista_divergencias, limite, offset):
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
        "listas": {
            "tipo": tipo,
            "limite": limite,
            "offset": offset,
            "concordancias": lista_concordancias,
            "divergencias": lista_divergencias,
        },
    }
