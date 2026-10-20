"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/deputado.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas da ficha do deputado: os dados cadastrais e a lista dos
    parlamentares com quem ele mais concorda numa execucao.

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao, para o endpoint GET /anos/{ano}/deputados/{id}.
"""


def buscar_ficha(conexao, deputado_id):
    """Dados cadastrais do deputado, ou None se o id nao existe."""
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT deputado_id, nome, sigla_partido, sigla_uf, url_foto
            FROM app.deputado
            WHERE deputado_id = %(deputado_id)s
            """,
            {"deputado_id": deputado_id},
        )
        return cursor.fetchone()


def listar_mais_similares(conexao, execucao_id, deputado_id, limite):
    """
    Deputados com quem ele mais concorda na execucao, do maior percentual
    para o menor. Vem da concordancia completa, e nao so das arestas do
    grafo: assim quem tem o melhor par abaixo do corte nao fica sem lista.

    O par e guardado uma vez so, com o menor id em deputado_a, entao o
    deputado pedido pode estar de qualquer um dos dois lados. A subconsulta
    usa um CASE para devolver sempre "o outro" do par, e so depois busca o
    nome dele em app.deputado.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT d.deputado_id, d.nome, d.sigla_partido,
                   par.percentual, par.votacoes_em_comum
            FROM (
                SELECT CASE WHEN c.deputado_a = %(deputado_id)s THEN c.deputado_b
                            ELSE c.deputado_a END AS outro_id,
                       c.percentual,
                       c.votacoes_em_comum
                FROM app.concordancia c
                WHERE c.execucao_id = %(execucao_id)s
                  AND %(deputado_id)s IN (c.deputado_a, c.deputado_b)
            ) par
            JOIN app.deputado d ON d.deputado_id = par.outro_id
            ORDER BY par.percentual DESC, d.nome
            LIMIT %(limite)s
            """,
            {"execucao_id": execucao_id, "deputado_id": deputado_id, "limite": limite},
        )
        return cursor.fetchall()
