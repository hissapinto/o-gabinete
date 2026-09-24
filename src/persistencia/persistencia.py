"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/persistencia/persistencia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Camada de persistencia. Unico modulo que conhece o formato do arquivo
    grafo.txt, conforme especificado no enunciado:

        <tipo do grafo>
        <n>
        <indice> "<rotulo>"        (n linhas)
        <m>
        <v> <w> <peso>             (m linhas)

    O tipo utilizado e o 2 (grafo nao orientado com peso na aresta), por isso
    as linhas de vertice nao trazem peso. Por ser um grafo nao orientado, cada
    aresta aparece uma unica vez no arquivo.

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao da leitura e da gravacao.
"""

import os

from grafo import GrafoPonderadoND

CAMINHO_PADRAO = os.path.join("dados", "grafo.txt")


class ErroDeArquivo(Exception):
    """Erro de leitura ou de formato do arquivo do grafo."""


# LEITURA
def ler(caminho=CAMINHO_PADRAO):
    """Le o arquivo e devolve um GrafoPonderadoND montado."""
    if not os.path.exists(caminho):
        raise ErroDeArquivo(f"arquivo nao encontrado: {caminho}")

    with open(caminho, "r", encoding="utf-8") as arquivo:
        linhas = [linha.strip() for linha in arquivo if linha.strip() != ""]

    if len(linhas) < 2:
        raise ErroDeArquivo("arquivo vazio ou incompleto")

    posicao = 0

    # tipo do grafo
    tipo = _inteiro(linhas[posicao], "tipo do grafo")
    posicao += 1
    if tipo != GrafoPonderadoND.TIPO:
        raise ErroDeArquivo(
            f"tipo {tipo} nao suportado (esperado {GrafoPonderadoND.TIPO})"
        )

    # quantidade de vertices
    n = _inteiro(linhas[posicao], "numero de vertices")
    posicao += 1

    grafo = GrafoPonderadoND(n)

    # rotulos dos vertices
    for i in range(n):
        if posicao >= len(linhas):
            raise ErroDeArquivo("faltam linhas de vertice")
        indice, rotulo = _separaVertice(linhas[posicao])
        if not grafo.existeV(indice):
            raise ErroDeArquivo(f"indice de vertice invalido: {indice}")
        grafo.rotulos[indice] = rotulo
        posicao += 1

    # quantidade de arestas
    if posicao >= len(linhas):
        raise ErroDeArquivo("faltou o numero de arestas")
    m = _inteiro(linhas[posicao], "numero de arestas")
    posicao += 1

    # arestas
    for _ in range(m):
        if posicao >= len(linhas):
            raise ErroDeArquivo("faltam linhas de aresta")
        partes = linhas[posicao].split()
        if len(partes) < 3:
            raise ErroDeArquivo(f"aresta mal formada: {linhas[posicao]}")
        v = _inteiro(partes[0], "vertice de origem")
        w = _inteiro(partes[1], "vertice de destino")
        peso = _inteiro(partes[2], "peso da aresta")
        if not grafo.insereA(v, w, peso):
            raise ErroDeArquivo(f"aresta invalida: {v} {w}")
        posicao += 1

    return grafo


# GRAVACAO
def gravar(grafo, caminho=CAMINHO_PADRAO):
    """Grava o grafo da memoria no arquivo, no mesmo formato da leitura."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    arestas = grafo.arestas()

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"{GrafoPonderadoND.TIPO}\n")
        arquivo.write(f"{grafo.n}\n")
        for v in range(grafo.n):
            arquivo.write(f'{v} "{grafo.rotulos[v]}"\n')
        arquivo.write(f"{len(arestas)}\n")
        for (v, w, peso) in arestas:
            arquivo.write(f"{v} {w} {peso}\n")

    return len(arestas)


def conteudo(caminho=CAMINHO_PADRAO):
    """Devolve o conteudo bruto do arquivo, para a opcao (g) do menu."""
    if not os.path.exists(caminho):
        raise ErroDeArquivo(f"arquivo nao encontrado: {caminho}")
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


# AUXILIARES
def _inteiro(texto, descricao):
    """Converte para inteiro, com mensagem clara em caso de erro."""
    try:
        return int(texto.split()[0])
    except (ValueError, IndexError):
        raise ErroDeArquivo(f"{descricao} invalido: '{texto}'")


def _separaVertice(linha):
    """
    Separa uma linha de vertice em (indice, rotulo).
    Aceita rotulo entre aspas ou sem aspas.
    """
    if '"' in linha:
        antes, _, resto = linha.partition('"')
        rotulo = resto.rpartition('"')[0]
        indice = _inteiro(antes, "indice do vertice")
    else:
        partes = linha.split(maxsplit=1)
        indice = _inteiro(partes[0], "indice do vertice")
        rotulo = partes[1].strip() if len(partes) > 1 else ""
    return indice, rotulo