"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/main.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Ponto de entrada da aplicacao. Nao pertence a nenhuma camada: apenas
    prepara os caminhos de importacao, define a pasta de trabalho como a
    raiz do projeto e inicia o menu.

    Execucao, a partir de qualquer pasta:
        python src/main.py

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao.
"""

import os
import sys

# Pasta onde este arquivo esta (src/) e a raiz do projeto (um nivel acima).
PASTA_SRC = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SRC)

# Permite importar os modulos das camadas pelo nome, sem pacotes.
for camada in ("negocio", "persistencia", "apresentacao"):
    sys.path.insert(0, os.path.join(PASTA_SRC, camada))

# Garante que 'dados/grafo.txt' seja encontrado a partir da raiz do projeto.
os.chdir(RAIZ)

import menu  # noqa: E402  (import depois de ajustar o sys.path)


if __name__ == "__main__":
    try:
        menu.executar()
    except KeyboardInterrupt:
        print("\n\n  Aplicacao interrompida pelo usuario.\n")