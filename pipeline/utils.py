"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/utils.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Utilitario compartilhado do pipeline. Localiza a raiz do projeto subindo
    diretorios ate encontrar o requirements.txt, para que os caminhos de
    dados funcionem independente da pasta de onde o script e executado.

Historico de alteracoes:
    14/09/2026 - Kaique - Criacao da funcao que localiza a raiz do projeto.
"""

from pathlib import Path


def encontrar_raiz(marcador="requirements.txt"):
    caminho = Path.cwd()
    while not (caminho / marcador).exists():
        caminho = caminho.parent
    return caminho


RAIZ = encontrar_raiz()