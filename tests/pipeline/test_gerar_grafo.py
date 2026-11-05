"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_gerar_grafo.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da montagem do grafo: quais arestas entram, com que peso e em que
    ordem os vertices ficam.

    A ordem dos vertices nao e cosmetica. O escolher_arestas desempata pela
    posicao do vertice, entao ordenar antes de escolher e o que garante que o
    grafo.txt e as arestas gravadas no banco sejam os mesmos -- os dois passam
    por montar_grafo justamente por isso.

    Inclui tambem um teste de ida e volta entre os dois subsistemas: o que o
    gravar_grafo escreve tem de ser legivel pela persistencia da aplicacao de
    terminal, que e o unico ponto de contato entre eles.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

import numpy as np
import pandas as pd
import pytest

import persistencia
from gerar_grafo import (
    chave_alfabetica,
    descartar_sem_par,
    escolher_arestas,
    gravar_grafo,
    montar_grafo,
    montar_rotulos,
)

NAN = np.nan


# --- ordenacao alfabetica --------------------------------------------------

def test_chave_ignora_acento():
    assert chave_alfabetica("Átila") == chave_alfabetica("Atila")


def test_chave_ignora_maiusculas():
    assert chave_alfabetica("ANA") == chave_alfabetica("ana")


def test_chave_ordena_acentuado_junto_do_sem_acento():
    nomes = ["Bruno", "Átila", "Ana"]

    assert sorted(nomes, key=chave_alfabetica) == ["Ana", "Átila", "Bruno"]


# --- descarte de quem nao tem par -----------------------------------------

def test_descarta_deputado_sem_nenhum_par_valido():
    ids = np.array([10, 20, 30])
    C = np.array([
        [NAN, 80.0, NAN],
        [80.0, NAN, NAN],
        [NAN, NAN, NAN],   # 30 nao tem par
    ])

    restantes, reduzida, descartados = descartar_sem_par(ids, C)

    assert list(restantes) == [10, 20]
    assert reduzida.shape == (2, 2)
    assert descartados == 1


def test_descarte_nao_altera_a_matriz_recebida():
    ids = np.array([10, 20])
    C = np.array([[5.0, 80.0], [80.0, 5.0]])
    original = C.copy()

    descartar_sem_par(ids, C)

    assert np.array_equal(C, original), "a diagonal foi apagada na matriz do chamador"


def test_ninguem_descartado_quando_todos_tem_par():
    ids = np.array([10, 20])
    C = np.array([[NAN, 80.0], [80.0, NAN]])

    restantes, _, descartados = descartar_sem_par(ids, C)

    assert list(restantes) == [10, 20]
    assert descartados == 0


# --- escolha das arestas ---------------------------------------------------

def test_liga_apenas_acima_da_concordancia_minima():
    C = np.array([
        [NAN, 90.0, 50.0],
        [90.0, NAN, 60.0],
        [50.0, 60.0, NAN],
    ])

    arestas = escolher_arestas(C, k=2, minimo=75)

    assert set(arestas) == {(0, 1)}


def test_peso_e_o_percentual_arredondado():
    C = np.array([[NAN, 83.6], [83.6, NAN]])

    assert escolher_arestas(C, k=1, minimo=75) == {(0, 1): 84}


def test_par_vem_sempre_com_o_menor_indice_primeiro():
    C = np.array([[NAN, 90.0], [90.0, NAN]])

    assert all(v < w for (v, w) in escolher_arestas(C, k=1, minimo=75))


VIZINHANCA = np.array([
    [NAN, 95.0, 90.0, 85.0],
    [95.0, NAN, 80.0, 80.0],
    [90.0, 80.0, NAN, 80.0],
    [85.0, 80.0, 80.0, NAN],
])


def test_aresta_entra_pela_escolha_de_qualquer_um_dos_dois():
    """
    O k limita quantos vizinhos cada vertice escolhe, e nao quantos o
    escolhem. Com k=1 o vertice 0 so escolhe o 1, mas as arestas (0,2) e (0,3)
    aparecem assim mesmo, porque para o 2 e para o 3 o vertice 0 e o mais
    parecido. O grafo resultante nao e regular.
    """
    arestas = escolher_arestas(VIZINHANCA, k=1, minimo=75)

    assert set(arestas) == {(0, 1), (0, 2), (0, 3)}


def test_k_maior_admite_mais_arestas():
    poucas = escolher_arestas(VIZINHANCA, k=1, minimo=75)
    muitas = escolher_arestas(VIZINHANCA, k=3, minimo=75)

    assert len(poucas) < len(muitas)
    assert set(poucas).issubset(set(muitas))


def test_matriz_sem_par_valido_nao_gera_aresta():
    C = np.array([[NAN, 10.0], [10.0, NAN]])

    assert escolher_arestas(C, k=2, minimo=75) == {}


# --- montagem completa -----------------------------------------------------

def test_vertices_ficam_em_ordem_alfabetica():
    ids = np.array([10, 20, 30])
    C = np.array([
        [NAN, 90.0, 80.0],
        [90.0, NAN, 85.0],
        [80.0, 85.0, NAN],
    ])
    rotulos = ["Carla (PT-SP)", "Ana (PL-RJ)", "Bruno (MDB-MG)"]

    ids_ord, rotulos_ord, _ = montar_grafo(ids, C, rotulos)

    assert rotulos_ord == ["Ana (PL-RJ)", "Bruno (MDB-MG)", "Carla (PT-SP)"]
    assert ids_ord == [20, 30, 10], "os ids acompanham a nova ordem dos rotulos"


def test_arestas_usam_os_indices_depois_da_ordenacao():
    ids = np.array([10, 20])
    C = np.array([[NAN, 90.0], [90.0, NAN]])
    rotulos = ["Bruno", "Ana"]

    ids_ord, _, arestas = montar_grafo(ids, C, rotulos)

    assert ids_ord == [20, 10]
    assert set(arestas) == {(0, 1)}
    assert arestas[(0, 1)] == 90


def test_montar_grafo_e_estavel_entre_chamadas():
    """
    O grafo.txt e a carga no banco chamam montar_grafo separadamente. Se duas
    chamadas com a mesma entrada dessem resultados diferentes, as arestas do
    arquivo e as do banco divergiriam.
    """
    ids = np.array([10, 20, 30])
    C = np.array([
        [NAN, 90.0, 90.0],
        [90.0, NAN, 90.0],
        [90.0, 90.0, NAN],
    ])
    rotulos = ["Carla", "Ana", "Bruno"]

    primeira = montar_grafo(ids, C, rotulos)
    segunda = montar_grafo(ids, C, rotulos)

    assert primeira[0] == segunda[0]
    assert primeira[1] == segunda[1]
    assert primeira[2] == segunda[2]


# --- rotulos ---------------------------------------------------------------

def test_rotulo_tem_nome_partido_e_uf():
    deputados = pd.DataFrame([
        (10, "Ana Ribeiro", "PT", "SP"),
    ], columns=["deputado_id", "deputado_nome", "deputado_siglaPartido", "deputado_siglaUf"])

    assert montar_rotulos(np.array([10]), deputados) == ["Ana Ribeiro (PT-SP)"]


def test_aspas_no_nome_viram_apostrofo():
    """O grafo.txt delimita o rotulo com aspas; uma aspa no nome quebraria a linha."""
    deputados = pd.DataFrame([
        (10, 'Jose "Ze" Silva', "PP", "BA"),
    ], columns=["deputado_id", "deputado_nome", "deputado_siglaPartido", "deputado_siglaUf"])

    assert montar_rotulos(np.array([10]), deputados) == ["Jose 'Ze' Silva (PP-BA)"]


# --- contato com a aplicacao de terminal -----------------------------------

def test_arquivo_gravado_e_legivel_pela_aplicacao_de_terminal(tmp_path):
    """
    O pipeline grava o grafo.txt e a aplicacao de terminal o le. Este e o
    unico ponto de contato entre os dois subsistemas, e nada mais o verifica.
    """
    rotulos = ["Ana Ribeiro (PT-SP)", "Bruno Castro (PL-RJ)", "Átila Dias (MDB-MG)"]
    arestas = {(0, 1): 90, (1, 2): 80}
    caminho = str(tmp_path / "grafo.txt")

    gravar_grafo(caminho, rotulos, arestas)
    lido = persistencia.ler(caminho)

    assert lido.n == 3
    assert lido.m == 2
    assert lido.rotulos == rotulos
    assert lido.peso(0, 1) == 90
    assert lido.peso(1, 2) == 80


def test_grafo_sem_aresta_tambem_e_legivel(tmp_path):
    caminho = str(tmp_path / "grafo.txt")

    gravar_grafo(caminho, ["Ana", "Bruno"], {})

    assert persistencia.ler(caminho).m == 0
