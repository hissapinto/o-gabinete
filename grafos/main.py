"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: grafos/main.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Ponto de entrada da aplicacao. Nao pertence a nenhuma camada: apenas
    prepara os caminhos de importacao, define a pasta de trabalho como a
    raiz do projeto e inicia o menu.

    Execucao, a partir de qualquer pasta:
        python grafos/main.py

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao.
    18/10/2026 - Isabela - Caminhos atualizados apos a renomeacao de src/ para grafos/.
"""

import os
import sys

# Pasta onde este arquivo esta (grafos/) e a raiz do projeto (um nivel acima).
PASTA_GRAFOS = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_GRAFOS)

# Permite importar os modulos das camadas pelo nome, sem pacotes.
for camada in ("negocio", "persistencia", "apresentacao"):
    sys.path.insert(0, os.path.join(PASTA_GRAFOS, camada))

# Garante que 'dados/grafo.txt' seja encontrado a partir da raiz do projeto.
os.chdir(RAIZ)

import menu  # noqa: E402  (import depois de ajustar o sys.path)


if __name__ == "__main__":
    try:
        menu.executar()
    except KeyboardInterrupt:
        print("\n\n  Aplicacao interrompida pelo usuario.\n")