"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/repositorios/execucao.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Consultas sobre a tabela app.execucao. So SQL: recebe a conexao de quem
    chama, nao trata erros e nao conhece HTTP.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao, com a listagem dos anos disponiveis.
"""


def listar_anos_disponiveis(conexao):
    """
    Anos que tem pelo menos uma execucao de um ano so (ano_inicio = ano_fim),
    cada ano uma vez, do mais recente ao mais antigo. Ex.: [{"ano": 2024}].
    """
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT ano_inicio AS ano
            FROM app.execucao
            WHERE ano_inicio = ano_fim
            ORDER BY ano DESC
            """
        )
        return cursor.fetchall()
