"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/servicos/erros.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Excecoes da camada de servico. Dizem o que aconteceu, sem conhecer HTTP;
    as rotas traduzem cada uma no status adequado.

Historico de alteracoes:
    17/10/2026 - Caio - Criacao.
"""


class NaoEncontrado(Exception):
    """O recurso pedido nao existe (ano sem grafo, deputado que nao votou no ano)."""
