"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/rotas/test_fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da rota GET /anos/{ano}/fora-do-grafo.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao.
"""

from tests import cenario


def test_fora_do_grafo_do_ano(cliente):
    resposta = cliente.get(f"/anos/{cenario.ANO}/fora-do-grafo")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo == {
        "ano": cenario.ANO,
        "total_votacoes": 7,
        "minimo_em_comum": 3,
        "deputados": [{
            "deputado_id": cenario.DIEGO, "nome": cenario.NOMES[cenario.DIEGO],
            "sigla_partido": "PP", "sigla_uf": "BA",
            "votacoes": 1, "artigo_17": 0, "motivo": "poucas_votacoes",
        }],
    }


def test_ninguem_do_grafo_aparece_na_lista(cliente):
    """Invariante: um deputado esta no grafo ou na lista dos de fora, nunca nos dois."""
    nos = {n["deputado_id"] for n in cliente.get(f"/anos/{cenario.ANO}/grafo").json()["nos"]}
    fora = {d["deputado_id"] for d in cliente.get(f"/anos/{cenario.ANO}/fora-do-grafo").json()["deputados"]}

    assert nos.isdisjoint(fora)


def test_ano_sem_grafo_devolve_404(cliente):
    resposta = cliente.get(f"/anos/{cenario.ANO_SEM_EXECUCAO}/fora-do-grafo")

    assert resposta.status_code == 404
    assert str(cenario.ANO_SEM_EXECUCAO) in resposta.json()["detail"]


def test_ano_nao_numerico_devolve_422(cliente):
    assert cliente.get("/anos/abc/fora-do-grafo").status_code == 422
