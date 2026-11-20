"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: grafos/negocio/blocos.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Solucao do problema (item 1 da parte 3): deteccao de blocos de votacao a
    partir da ARVORE GERADORA MAXIMA do grafo de similaridade.

    1. Algoritmo de Kruskal com conjuntos disjuntos (union-find): as arestas
       sao percorridas da MAIOR para a menor concordancia, e cada aresta que
       liga duas arvores diferentes entra na solucao. Como o grafo e
       desconexo, o resultado e uma floresta geradora maxima, com uma arvore
       por componente conexa.
    2. Agrupamento por corte da arvore (Zahn, 1971): a floresta guarda, para
       cada par de deputados, o caminho de maior afinidade minima entre eles.
       Cortar as arestas mais fracas dessa floresta separa os grupos menos
       ligados entre si. Cada corte so e aceito se os dois lados ficarem com
       pelo menos 'tamanho_minimo' deputados, para nao isolar um deputado
       sozinho (o efeito de encadeamento do agrupamento por ligacao simples).
    3. Avaliacao: para cada bloco sao calculados tamanho, composicao
       partidaria, concordancia media das arestas internas, e para a
       particao toda a modularidade de Newman.

    Nao guarda dados nem imprime nada: recebe um GrafoPonderadoND e devolve
    estruturas simples, que a camada de apresentacao formata.

Historico de alteracoes:
    19/11/2026 - Kaique - Criacao: Kruskal, corte da arvore, resumo dos blocos,
                          modularidade e analise de sensibilidade.
    20/11/2026 - Kaique - Componente ja separada pelos votos conta como bloco
                          mesmo menor que o tamanho minimo, que passa a valer
                          so para os cortes (o PSOL nao vira mais "avulso").
"""

import re

from filaCircular import FilaCircular

# Rotulo no formato 'Nome (PARTIDO-UF)'; o partido e o trecho antes do hifen.
_PADRAO_PARTIDO = re.compile(r"\(([^()]+)-([A-Z]{2})\)\s*$")


# CONJUNTOS DISJUNTOS (UNION-FIND)
class ConjuntosDisjuntos:
    """
    Particao dos vertices em conjuntos, usada pelo Kruskal para saber, em
    tempo quase constante, se uma aresta fecharia um ciclo.
    Usa compressao de caminho e uniao por tamanho.
    """

    def __init__(self, n):
        self.pai = list(range(n))
        self.tamanho = [1] * n

    def encontrar(self, v):
        """Devolve o representante do conjunto de v."""
        raiz = v
        while self.pai[raiz] != raiz:
            raiz = self.pai[raiz]
        # compressao de caminho: todos no caminho passam a apontar para a raiz
        while self.pai[v] != raiz:
            proximo = self.pai[v]
            self.pai[v] = raiz
            v = proximo
        return raiz

    def unir(self, v, w):
        """Une os conjuntos de v e w. Devolve False se ja estavam juntos."""
        rv, rw = self.encontrar(v), self.encontrar(w)
        if rv == rw:
            return False
        if self.tamanho[rv] < self.tamanho[rw]:
            rv, rw = rw, rv
        self.pai[rw] = rv
        self.tamanho[rv] += self.tamanho[rw]
        return True


# ARVORE GERADORA MAXIMA (KRUSKAL)
def arvore_geradora_maxima(grafo):
    """
    Devolve a floresta geradora maxima como lista de arestas (v, w, peso),
    na ordem em que o Kruskal as aceitou (maior peso primeiro).

    Empates de peso sao resolvidos pelos indices dos vertices, para que o
    resultado seja sempre o mesmo para o mesmo arquivo.
    A floresta tem n - c arestas, sendo c o numero de componentes conexas.
    """
    arestas = sorted(grafo.arestas(), key=lambda a: (-a[2], a[0], a[1]))
    conjuntos = ConjuntosDisjuntos(grafo.n)

    floresta = []
    for (v, w, peso) in arestas:
        if conjuntos.unir(v, w):
            floresta.append((v, w, peso))
            if len(floresta) == grafo.n - 1:
                break  # arvore completa: nenhuma outra aresta pode entrar
    return floresta


def peso_total(arestas):
    """Soma dos pesos de uma lista de arestas (v, w, peso)."""
    return sum(p for (_v, _w, p) in arestas)


# AGRUPAMENTO POR CORTE DA ARVORE
def _adjacencia(n, arestas):
    """Monta conjuntos de vizinhos a partir de uma lista de arestas."""
    adj = [set() for _ in range(n)]
    for (v, w, _p) in arestas:
        adj[v].add(w)
        adj[w].add(v)
    return adj


def _alcancaveis(adj, origem):
    """Vertices alcancaveis a partir de origem (busca em largura com a FilaCircular)."""
    visitados = {origem}
    fila = FilaCircular(len(adj) + 1)
    fila.enqueue(origem)
    while not fila.isEmpty():
        v = fila.dequeue()
        for w in adj[v]:
            if w not in visitados:
                visitados.add(w)
                fila.enqueue(w)
    return visitados


def _componentes(adj):
    """Componentes conexas de uma adjacencia, cada uma em ordem crescente."""
    n = len(adj)
    visto = [False] * n
    componentes = []
    for v in range(n):
        if not visto[v]:
            comp = _alcancaveis(adj, v)
            for x in comp:
                visto[x] = True
            componentes.append(sorted(comp))
    return componentes


def detectar_blocos(grafo, num_blocos=4, tamanho_minimo=10):
    """
    Divide os deputados em blocos de votacao cortando a floresta geradora
    maxima nas arestas mais fracas.

    num_blocos     : quantidade de blocos desejada. As componentes conexas
                     com pelo menos 2 deputados ja contam como blocos: foram
                     os proprios votos que as separaram.
    tamanho_minimo : um corte so vale se os dois lados ficarem com pelo menos
                     essa quantidade de deputados. O minimo vale so para os
                     cortes, para que eles nao isolem um deputado de cada vez.
                     Deputados sem nenhuma aresta sao devolvidos como grupos
                     avulsos e nao contam para num_blocos.

    Devolve um dicionario com:
        'floresta' : arestas da floresta geradora maxima
        'cortes'   : arestas cortadas, da mais fraca para a mais forte
        'blocos'   : lista de grupos (listas de vertices), do maior ao menor;
                     os 'significativos' primeiros sao os blocos de verdade
        'significativos' : quantos grupos contam como bloco
    Se nao houver cortes validos suficientes, 'significativos' fica menor
    que num_blocos; quem chama compara os dois.
    """
    if num_blocos < 1:
        raise ValueError("o numero de blocos deve ser pelo menos 1")
    if tamanho_minimo < 1:
        raise ValueError("o tamanho minimo deve ser pelo menos 1")

    floresta = arvore_geradora_maxima(grafo)
    adj = _adjacencia(grafo.n, floresta)
    # componentes ja separadas contam como bloco (um deputado sozinho, nao);
    # cada corte valido divide um bloco em dois, somando exatamente um
    quantidade = sum(1 for c in _componentes(adj) if len(c) >= 2)

    cortes = []
    # da aresta mais fraca para a mais forte; empate pelos indices
    for (v, w, peso) in sorted(floresta, key=lambda a: (a[2], a[0], a[1])):
        if quantidade >= num_blocos:
            break

        # corta e confere o tamanho dos dois lados
        adj[v].discard(w)
        adj[w].discard(v)
        lado_v = len(_alcancaveis(adj, v))
        lado_w = len(_alcancaveis(adj, w))

        if lado_v >= tamanho_minimo and lado_w >= tamanho_minimo:
            cortes.append((v, w, peso))
            quantidade += 1
        else:
            adj[v].add(w)   # corte recusado: devolve a aresta
            adj[w].add(v)

    blocos = sorted(_componentes(adj), key=lambda b: (-len(b), b[0]))
    return {"floresta": floresta, "cortes": cortes, "blocos": blocos,
            "significativos": quantidade}


# AVALIACAO DOS BLOCOS
def partido_do_rotulo(rotulo):
    """Extrai o partido de um rotulo 'Nome (PARTIDO-UF)'; '?' se nao houver."""
    achado = _PADRAO_PARTIDO.search(rotulo or "")
    return achado.group(1) if achado else "?"


def blocos_por_partido(grafo):
    """
    Particao de referencia: um bloco por partido, segundo o rotulo. Serve
    para comparar a modularidade dos blocos achados com a dos partidos.
    """
    por_partido = {}
    for v in range(grafo.n):
        por_partido.setdefault(partido_do_rotulo(grafo.rotulo(v)), []).append(v)
    return sorted(por_partido.values(), key=lambda b: (-len(b), b[0]))


def bloco_de_cada_vertice(n, blocos):
    """Vetor com o numero do bloco de cada vertice."""
    indice = [-1] * n
    for b, bloco in enumerate(blocos):
        for v in bloco:
            indice[v] = b
    return indice


def resumo_dos_blocos(grafo, blocos):
    """
    Para cada bloco devolve um dicionario com:
        tamanho, partidos (lista (partido, qtde) do mais ao menos frequente),
        arestas_internas, concordancia_media (das arestas internas, ou None),
        arestas_externas (arestas do grafo original que saem do bloco).
    """
    de_qual = bloco_de_cada_vertice(grafo.n, blocos)
    internas = [0] * len(blocos)
    soma_pesos = [0] * len(blocos)
    externas = [0] * len(blocos)

    for (v, w, p) in grafo.arestas():
        bv, bw = de_qual[v], de_qual[w]
        if bv == bw:
            internas[bv] += 1
            soma_pesos[bv] += p
        else:
            externas[bv] += 1
            externas[bw] += 1

    resumos = []
    for b, bloco in enumerate(blocos):
        contagem = {}
        for v in bloco:
            partido = partido_do_rotulo(grafo.rotulo(v))
            contagem[partido] = contagem.get(partido, 0) + 1
        partidos = sorted(contagem.items(), key=lambda par: (-par[1], par[0]))

        resumos.append({
            "tamanho": len(bloco),
            "partidos": partidos,
            "arestas_internas": internas[b],
            "concordancia_media": soma_pesos[b] / internas[b] if internas[b] else None,
            "arestas_externas": externas[b],
        })
    return resumos


def modularidade(grafo, blocos):
    """
    Modularidade de Newman (sem peso) da particao em blocos:

        Q = soma sobre os blocos de [ L_b / m  -  (D_b / 2m)^2 ]

    L_b e o numero de arestas internas ao bloco b e D_b a soma dos graus dos
    seus vertices. Q perto de 0 indica particao nao melhor que o acaso; acima
    de 0,3 costuma indicar estrutura de grupos clara (NEWMAN, 2006).
    """
    if grafo.m == 0:
        return 0.0

    de_qual = bloco_de_cada_vertice(grafo.n, blocos)
    internas = [0] * len(blocos)
    soma_graus = [0] * len(blocos)

    for v in range(grafo.n):
        soma_graus[de_qual[v]] += grafo.grau(v)
    for (v, w, _p) in grafo.arestas():
        if de_qual[v] == de_qual[w]:
            internas[de_qual[v]] += 1

    m = grafo.m
    return sum(internas[b] / m - (soma_graus[b] / (2 * m)) ** 2
               for b in range(len(blocos)))


def sensibilidade(grafo, lista_num_blocos, lista_tamanho_minimo):
    """
    Roda detectar_blocos para cada combinacao de parametros e devolve uma
    lista de dicionarios com num_blocos pedido, tamanho_minimo, blocos
    obtidos (so os significativos), tamanhos de todos os grupos e
    modularidade. Serve para verificar se a conclusao depende da escolha dos
    parametros.
    """
    linhas = []
    for minimo in lista_tamanho_minimo:
        for k in lista_num_blocos:
            resultado = detectar_blocos(grafo, k, minimo)
            blocos = resultado["blocos"]
            linhas.append({
                "num_blocos": k,
                "tamanho_minimo": minimo,
                "obtidos": resultado["significativos"],
                "tamanhos": [len(b) for b in blocos],
                "modularidade": modularidade(grafo, blocos),
            })
    return linhas
