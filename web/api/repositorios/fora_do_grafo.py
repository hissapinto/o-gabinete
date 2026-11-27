"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/fora_do_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas dos deputados que votaram no ano mas nao entraram no grafo:
    nenhum par deles chegou ao minimo de votacoes em comum, entao eles nao
    aparecem em app.concordancia da execucao. So SQL: recebe a conexao de
    quem chama, nao trata erros e nao conhece HTTP.

Historico de alteracoes:
    27/11/2026 - Kaique - Criacao, para o endpoint GET /anos/{ano}/fora-do-grafo.
"""


def listar_fora_do_grafo(conexao, execucao_id, ano):
    """
    Deputados com voto no ano que nao aparecem em nenhum par da execucao.

    Para cada um: votacoes (votos que entram na conta da concordancia: Sim,
    Nao ou Obstrucao, a RN01) e artigo_17 (votacoes em que ele presidiu a
    sessao). O partido e o do voto mais recente do ano, que e o que o
    deputado tinha naquele ano; sem partido no voto, vale o do cadastro.
    Ordem: quem votou mais primeiro, depois por nome.

    Os votos sao agrupados por deputado antes de olhar o grafo, e a presenca
    no grafo e testada com NOT EXISTS sobre os indices de app.concordancia
    (chave primaria para deputado_a e idx_concordancia_b para deputado_b).
    Um NOT IN contra a uniao dos pares (cerca de 136 mil por ano) levava
    minutos no banco real.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            WITH votos_do_ano AS (
                SELECT vo.deputado_id, vo.voto, vo.sigla_partido, v.data, v.votacao_id
                FROM app.voto vo
                JOIN app.votacao v USING (votacao_id)
                WHERE v.ano = %(ano)s
            ),
            por_deputado AS (
                SELECT deputado_id,
                       count(*) FILTER (WHERE voto IN ('Sim', 'Não', 'Obstrução')) AS votacoes,
                       count(*) FILTER (WHERE voto = 'Artigo 17') AS artigo_17
                FROM votos_do_ano
                GROUP BY deputado_id
            ),
            partido_do_ano AS (
                SELECT DISTINCT ON (deputado_id) deputado_id, sigla_partido
                FROM votos_do_ano
                WHERE sigla_partido IS NOT NULL
                ORDER BY deputado_id, data DESC, votacao_id DESC
            )
            SELECT d.deputado_id, d.nome,
                   COALESCE(p.sigla_partido, d.sigla_partido) AS sigla_partido,
                   d.sigla_uf, pd.votacoes, pd.artigo_17
            FROM por_deputado pd
            JOIN app.deputado d USING (deputado_id)
            LEFT JOIN partido_do_ano p USING (deputado_id)
            WHERE NOT EXISTS (SELECT 1 FROM app.concordancia c
                              WHERE c.execucao_id = %(execucao_id)s AND c.deputado_a = pd.deputado_id)
              AND NOT EXISTS (SELECT 1 FROM app.concordancia c
                              WHERE c.execucao_id = %(execucao_id)s AND c.deputado_b = pd.deputado_id)
            ORDER BY pd.votacoes DESC, d.nome
            """,
            {"ano": ano, "execucao_id": execucao_id},
        )
        return cursor.fetchall()


def contar_votacoes_do_ano(conexao, ano):
    """
    Quantas votacoes nominais de merito o ano tem: as de app.votacao com pelo
    menos um voto individual. A carga grava tambem votacoes de merito sem voto
    nominal (simbolicas), que nao entram em nenhuma conta de concordancia; em
    2024 sao 817 votacoes gravadas e 141 nominais.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*) AS total
            FROM app.votacao v
            WHERE v.ano = %(ano)s
              AND EXISTS (SELECT 1 FROM app.voto vo WHERE vo.votacao_id = v.votacao_id)
            """,
            {"ano": ano},
        )
        return cursor.fetchone()["total"]


def buscar_minimo_em_comum(conexao, execucao_id):
    """Minimo de votacoes em comum que a execucao exigiu para um par entrar no grafo."""
    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT minimo_votacoes_em_comum FROM app.execucao WHERE execucao_id = %(execucao_id)s",
            {"execucao_id": execucao_id},
        )
        return cursor.fetchone()["minimo_votacoes_em_comum"]
