"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/banco.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Conexao com o banco PostgreSQL. Unico lugar que conhece a DATABASE_URL;
    rotas e repositorios importam conectar() daqui.

Historico de alteracoes:
    17/10/2026 - Caio - Conexao movida do main.py para modulo proprio.
"""

import os

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]


def conectar():
    """Abre uma conexao que devolve cada linha como dicionario."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
