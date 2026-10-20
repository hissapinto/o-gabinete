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

    A regra de concordancia (RN01) aparece em listar_votacoes_do_par e precisa
    ficar igual a do pipeline/similaridade.py: Obstrucao conta como voto
    contra; Abstencao e Artigo 17 ficam fora da conta.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao, para o endpoint de concordancia do par.
    19/10/2026 - Isabela - listar_divergencias virou listar_votacoes_do_par,
                           que tambem lista as votacoes em que os dois
                           concordaram, para a tela de comparacao mostrar as
                           duas listas como o wireframe 4.3 descreve.
    19/10/2026 - Isabela - limite opcional: None traz a lista inteira.
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


def listar_votacoes_do_par(conexao, ano, deputado_a, deputado_b, concordaram, limite, offset):
    """
    Votacoes do ano em que os dois votaram de verdade (Sim, Nao ou Obstrucao),
    da mais recente para a mais antiga, paginadas.

    concordaram escolhe o lado da lista: True traz as votacoes em que os dois
    votaram do mesmo jeito, False as votacoes em que divergiram.

    limite None traz a lista inteira: no PostgreSQL, LIMIT NULL equivale a nao
    ter clausula LIMIT, e OFFSET NULL equivale a OFFSET 0. Por isso o limite
    opcional nao exige montar duas consultas diferentes.

    Depois do filtro de votos so sobra "a favor" (Sim) ou "contra" (Nao,
    Obstrucao); por isso concordar e os dois terem votado Sim, ou nenhum dos
    dois ter votado Sim. Um par Nao e Obstrucao concorda, porque a RN01 trata
    Obstrucao como voto contra -- e o motivo de a consulta devolver voto_a e
    voto_b, para a tela poder mostrar o voto literal de cada um e nao apenas o
    rotulo de concordancia.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT v.votacao_id, v.data, v.descricao,
                   va.voto AS voto_a, vb.voto AS voto_b,
                   (va.voto = 'Sim') = (vb.voto = 'Sim') AS concordaram
            FROM app.voto va
            JOIN app.voto vb   ON vb.votacao_id = va.votacao_id
                              AND vb.deputado_id = %(deputado_b)s
            JOIN app.votacao v ON v.votacao_id = va.votacao_id
            WHERE va.deputado_id = %(deputado_a)s
              AND v.ano = %(ano)s
              AND va.voto IN ('Sim', 'Não', 'Obstrução')
              AND vb.voto IN ('Sim', 'Não', 'Obstrução')
              AND ((va.voto = 'Sim') = (vb.voto = 'Sim')) = %(concordaram)s
            ORDER BY v.data DESC, v.votacao_id DESC
            LIMIT %(limite)s OFFSET %(offset)s
            """,
            {
                "ano": ano,
                "deputado_a": deputado_a,
                "deputado_b": deputado_b,
                "concordaram": concordaram,
                "limite": limite,
                "offset": offset,
            },
        )
        return cursor.fetchall()
