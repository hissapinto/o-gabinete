"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/concordancia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas sobre a tabela app.concordancia, gravada pelo pipeline. So SQL:
    recebe a conexao de quem chama, nao trata erros e nao conhece HTTP.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao, para o endpoint de concordancia do par.
"""


def buscar_concordancia(conexao, execucao_id, deputado_a, deputado_b):
    """
    Contadores e percentual do par na execucao, ou None se o par nao foi
    calculado. Espera deputado_a < deputado_b, como o banco guarda.
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT votacoes_em_comum, concordancias, percentual
            FROM app.concordancia
            WHERE execucao_id = %(execucao_id)s
              AND deputado_a = %(deputado_a)s
              AND deputado_b = %(deputado_b)s
            """,
            {"execucao_id": execucao_id, "deputado_a": deputado_a, "deputado_b": deputado_b},
        )
        return cursor.fetchone()
