"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas que montam o grafo de uma execucao: os vertices (deputados que
    aparecem em algum par de concordancia, com a posicao x/y do desenho) e as
    arestas (os k vizinhos mais parecidos de cada um, gravados pelo pipeline).

Historico de alteracoes:
    19/10/2026 - Isabela - Criacao, para o endpoint GET /anos/{ano}/grafo.
    04/11/2026 - Caio - Nos trazem x e y de app.posicao, da mesma execucao.
"""


def listar_nos(conexao, execucao_id):
    """
    Deputados que entraram no grafo da execucao: os que aparecem em algum par
    de app.concordancia, de qualquer um dos dois lados. Sem url_foto, que so
    a ficha do deputado usa.

    x e y vem de app.posicao da mesma execucao. O LEFT JOIN e de proposito:
    no sem posicao volta com x e y nulos em vez de sumir do grafo, e a camada
    de servico decide o que fazer com isso.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT d.deputado_id, d.nome, d.sigla_partido, d.sigla_uf, p.x, p.y
            FROM app.deputado d
            LEFT JOIN app.posicao p ON p.execucao_id = %(execucao_id)s
                                   AND p.deputado_id = d.deputado_id
            WHERE d.deputado_id IN (
                SELECT deputado_a FROM app.concordancia WHERE execucao_id = %(execucao_id)s
                UNION
                SELECT deputado_b FROM app.concordancia WHERE execucao_id = %(execucao_id)s
            )
            ORDER BY d.nome
            """,
            {"execucao_id": execucao_id},
        )
        return cursor.fetchall()


def listar_arestas(conexao, execucao_id):
    """
    Arestas do grafo da execucao, com o percentual de concordancia do par.
    O percentual vem de app.concordancia, e nao o peso inteiro de app.aresta,
    para a aresta mostrar o mesmo numero da ficha e do detalhe do par.
    As duas tabelas guardam o par com o menor id em deputado_a, entao o JOIN
    sempre encontra a linha correspondente.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT a.deputado_a, a.deputado_b, c.percentual
            FROM app.aresta a
            JOIN app.concordancia c ON c.execucao_id = a.execucao_id
                                   AND c.deputado_a  = a.deputado_a
                                   AND c.deputado_b  = a.deputado_b
            WHERE a.execucao_id = %(execucao_id)s
            ORDER BY a.deputado_a, a.deputado_b
            """,
            {"execucao_id": execucao_id},
        )
        return cursor.fetchall()
