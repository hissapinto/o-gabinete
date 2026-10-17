"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/voto.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas sobre os votos individuais (app.voto). So SQL: recebe a conexao
    de quem chama, nao trata erros e nao conhece HTTP.

    A regra de concordancia (RN01) aparece em listar_divergencias e precisa
    ficar igual a do pipeline/similaridade.py: Obstrucao conta como voto
    contra; Abstencao e Artigo 17 ficam fora da conta.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao, para o endpoint de concordancia do par.
"""


def deputados_que_votaram(conexao, ano, ids):
    """Devolve o conjunto dos ids, entre os informados, que votaram no ano."""
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT vo.deputado_id
            FROM app.voto vo
            JOIN app.votacao v USING (votacao_id)
            WHERE v.ano = %(ano)s
              AND vo.deputado_id = ANY(%(ids)s)
            """,
            {"ano": ano, "ids": list(ids)},
        )
        return {linha["deputado_id"] for linha in cursor.fetchall()}


def listar_divergencias(conexao, ano, deputado_a, deputado_b, limite, offset):
    """
    Votacoes do ano em que os dois votaram de verdade (Sim, Nao ou Obstrucao)
    e em lados opostos, da mais recente para a mais antiga, paginadas.
    Depois do filtro, so sobra "a favor" (Sim) ou "contra" (Nao, Obstrucao);
    por isso votar diferente e um ter votado Sim e o outro nao.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT v.votacao_id, v.data, v.descricao,
                   va.voto AS voto_a, vb.voto AS voto_b
            FROM app.voto va
            JOIN app.voto vb   ON vb.votacao_id = va.votacao_id
                              AND vb.deputado_id = %(deputado_b)s
            JOIN app.votacao v ON v.votacao_id = va.votacao_id
            WHERE va.deputado_id = %(deputado_a)s
              AND v.ano = %(ano)s
              AND va.voto IN ('Sim', 'Não', 'Obstrução')
              AND vb.voto IN ('Sim', 'Não', 'Obstrução')
              AND (va.voto = 'Sim') <> (vb.voto = 'Sim')
            ORDER BY v.data DESC, v.votacao_id DESC
            LIMIT %(limite)s OFFSET %(offset)s
            """,
            {"ano": ano, "deputado_a": deputado_a, "deputado_b": deputado_b,
             "limite": limite, "offset": offset},
        )
        return cursor.fetchall()
