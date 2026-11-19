"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: grafos/negocio/caracteristicas.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Caracteristicas do grafo modelado (item 2 da parte 3), cada uma com
    tecnicas vistas na disciplina:

    1. Grau dos vertices: minimo, maximo, medio, mediano, distribuicao,
       vertices de maior grau e conferencia do lema do aperto de maos.
    2. Grafo euleriano: teorema de Euler (conexo e todos os graus pares para
       ciclo; exatamente dois vertices de grau impar para percurso).
    3. Grafo hamiltoniano: condicoes necessarias (conexidade, grau minimo,
       vertices de articulacao) e suficientes (Dirac e Ore), com busca
       exaustiva por retrocesso apenas para grafos pequenos. Os vertices de
       articulacao e as pontes sao achados por busca em profundidade
       (Hopcroft e Tarjan).
    4. Coloracao: algoritmo de Welsh-Powell (limite superior do numero
       cromatico) e maior clique por Bron-Kerbosch com pivo (limite
       inferior).

    Nao guarda dados nem imprime nada: recebe um GrafoPonderadoND e devolve
    dicionarios que a camada de apresentacao formata.

Historico de alteracoes:
    19/11/2026 - Isabela - Criacao: grau, Euler, Hamilton, articulacoes,
                           pontes, Welsh-Powell e maior clique.
"""

from logica_grafos import componentes_conexas

# Acima disso a busca exaustiva por ciclo hamiltoniano fica cara demais
# (o problema e NP-completo); valem so as condicoes necessarias/suficientes.
LIMITE_BUSCA_HAMILTONIANA = 15


# 1. GRAU DOS VERTICES
def resumo_graus(grafo, quantos_maiores=10):
    """
    Estatisticas dos graus. Devolve um dicionario com minimo, maximo, medio,
    mediano, distribuicao ({grau: quantidade}), maiores (lista de (vertice,
    grau) dos de maior grau), soma (que tem de ser 2m), impares (quantidade
    de vertices de grau impar) e isolados.
    """
    graus = [grafo.grau(v) for v in range(grafo.n)]
    if not graus:
        return None

    ordenados = sorted(graus)
    meio = len(ordenados) // 2
    if len(ordenados) % 2 == 1:
        mediano = float(ordenados[meio])
    else:
        mediano = (ordenados[meio - 1] + ordenados[meio]) / 2

    distribuicao = {}
    for g in graus:
        distribuicao[g] = distribuicao.get(g, 0) + 1

    maiores = sorted(range(grafo.n), key=lambda v: (-graus[v], v))[:quantos_maiores]

    return {
        "minimo": ordenados[0],
        "maximo": ordenados[-1],
        "medio": sum(graus) / len(graus),
        "mediano": mediano,
        "distribuicao": dict(sorted(distribuicao.items())),
        "maiores": [(v, graus[v]) for v in maiores],
        "soma": sum(graus),
        "impares": sum(1 for g in graus if g % 2 == 1),
        "isolados": sum(1 for g in graus if g == 0),
    }


def faixas_de_grau(distribuicao, limites=(1, 2, 5, 10, 20, 50)):
    """
    Agrupa a distribuicao de graus em faixas para exibir no terminal.
    Devolve lista de (texto da faixa, quantidade de vertices).
    """
    faixas = []
    inicio = 0
    for limite in list(limites) + [None]:
        if limite is None:
            qtd = sum(q for g, q in distribuicao.items() if g >= inicio)
            texto = f"{inicio} ou mais"
        else:
            qtd = sum(q for g, q in distribuicao.items() if inicio <= g < limite)
            texto = f"{inicio}" if limite - inicio == 1 else f"{inicio} a {limite - 1}"
            inicio = limite
        faixas.append((texto, qtd))
    return faixas


# 2. GRAFO EULERIANO
def _conexo_sem_isolados(grafo):
    """
    Conexidade considerando so os vertices com aresta: vertices isolados nao
    impedem um percurso euleriano, porque o percurso passa pelas arestas.
    Devolve (conexo, quantidade de componentes com aresta).
    """
    com_aresta = [c for c in componentes_conexas(grafo) if grafo.grau(c[0]) > 0]
    return len(com_aresta) <= 1, len(com_aresta)


def analise_euleriana(grafo):
    """
    Aplica o teorema de Euler. Devolve um dicionario com:
        conexo, componentes_com_aresta, impares (lista de vertices de grau
        impar), classificacao ('euleriano', 'semi-euleriano' ou
        'nao euleriano'), motivo, e arestas_faltantes: quantas arestas, no
        minimo, teriam de ser acrescentadas para todos os graus ficarem pares
        (cada aresta nova corrige dois vertices impares).
    """
    impares = [v for v in range(grafo.n) if grafo.grau(v) % 2 == 1]
    conexo, componentes = _conexo_sem_isolados(grafo)

    if grafo.m == 0:
        classificacao = "nao euleriano"
        motivo = "o grafo nao tem arestas"
    elif not conexo:
        classificacao = "nao euleriano"
        motivo = (f"as arestas estao em {componentes} componentes; nenhum "
                  "percurso consegue passar de uma para a outra")
    elif len(impares) == 0:
        classificacao = "euleriano"
        motivo = "conexo e todos os vertices tem grau par (ciclo euleriano)"
    elif len(impares) == 2:
        classificacao = "semi-euleriano"
        motivo = ("conexo e exatamente dois vertices de grau impar "
                  f"(percurso euleriano de {impares[0]} ate {impares[1]})")
    else:
        classificacao = "nao euleriano"
        motivo = (f"{len(impares)} vertices de grau impar; o teorema de Euler "
                  "admite no maximo dois")

    return {
        "conexo": conexo,
        "componentes_com_aresta": componentes,
        "impares": impares,
        "classificacao": classificacao,
        "motivo": motivo,
        "arestas_faltantes": len(impares) // 2,
    }


# ARTICULACOES E PONTES (BUSCA EM PROFUNDIDADE)
def articulacoes_e_pontes(grafo):
    """
    Busca em profundidade de Hopcroft e Tarjan, em versao iterativa (uma
    pilha explicita no lugar da recursao).

    descoberta[v] : ordem em que v foi visitado
    baixo[v]      : menor ordem alcancavel a partir da subarvore de v usando
                    no maximo uma aresta de retorno

    Um vertice v (que nao e raiz) e articulacao se tem um filho w com
    baixo[w] >= descoberta[v]: sem v, w perde o caminho para cima. A raiz e
    articulacao se tem dois ou mais filhos. A aresta (v, w) e ponte se
    baixo[w] > descoberta[v].

    Devolve (lista de vertices de articulacao, lista de pontes (v, w, peso)).
    """
    n = grafo.n
    descoberta = [-1] * n
    baixo = [0] * n
    pai = [-1] * n
    articulacao = [False] * n
    pontes = []
    tempo = 0

    for raiz in range(n):
        if descoberta[raiz] != -1:
            continue

        descoberta[raiz] = baixo[raiz] = tempo
        tempo += 1
        filhos_da_raiz = 0
        # pilha de (vertice, lista de vizinhos, proxima posicao a examinar)
        pilha = [(raiz, grafo.vizinhos(raiz), 0)]

        while pilha:
            v, vizinhos, i = pilha[-1]
            if i < len(vizinhos):
                pilha[-1] = (v, vizinhos, i + 1)
                w = vizinhos[i][0]
                if descoberta[w] == -1:          # aresta de arvore: desce
                    pai[w] = v
                    descoberta[w] = baixo[w] = tempo
                    tempo += 1
                    if v == raiz:
                        filhos_da_raiz += 1
                    pilha.append((w, grafo.vizinhos(w), 0))
                elif w != pai[v]:                # aresta de retorno
                    baixo[v] = min(baixo[v], descoberta[w])
            else:                                # terminou v: sobe
                pilha.pop()
                p = pai[v]
                if p != -1:
                    baixo[p] = min(baixo[p], baixo[v])
                    if p != raiz and baixo[v] >= descoberta[p]:
                        articulacao[p] = True
                    if baixo[v] > descoberta[p]:
                        pontes.append((min(p, v), max(p, v), grafo.peso(p, v)))

        if filhos_da_raiz >= 2:
            articulacao[raiz] = True

    return [v for v in range(n) if articulacao[v]], sorted(pontes)


# 3. GRAFO HAMILTONIANO
def _ciclo_hamiltoniano_exaustivo(grafo):
    """
    Procura um ciclo hamiltoniano por retrocesso (backtracking), partindo do
    vertice 0. Devolve o ciclo como lista de vertices ou None. So deve ser
    usado em grafos pequenos.
    """
    n = grafo.n
    adj = [set(w for (w, _p) in grafo.vizinhos(v)) for v in range(n)]
    caminho = [0]
    usado = [False] * n
    usado[0] = True

    def estender():
        if len(caminho) == n:
            return 0 in adj[caminho[-1]]
        for w in sorted(adj[caminho[-1]]):
            if not usado[w]:
                usado[w] = True
                caminho.append(w)
                if estender():
                    return True
                caminho.pop()
                usado[w] = False
        return False

    return caminho + [0] if estender() else None


def analise_hamiltoniana(grafo):
    """
    Decide se o grafo admite ciclo hamiltoniano, usando:

    Condicoes NECESSARIAS (se alguma falha, nao ha ciclo):
        - pelo menos 3 vertices;
        - grafo conexo;
        - todo vertice com grau >= 2;
        - nenhum vertice de articulacao (o ciclo passaria duas vezes por ele).
    Condicoes SUFICIENTES (se alguma vale, ha ciclo):
        - Dirac: grau minimo >= n/2;
        - Ore: grau(u) + grau(v) >= n para todo par nao adjacente.
    Se nada decide e o grafo e pequeno, faz busca exaustiva.

    Tambem verifica o percurso hamiltoniano: exige grafo conexo e no maximo
    dois vertices de grau 1 (eles teriam de ser as pontas do percurso).

    Devolve um dicionario com as condicoes verificadas, a classificacao do
    ciclo ('hamiltoniano', 'nao hamiltoniano' ou 'inconclusivo'), o motivo,
    a situacao do percurso e as articulacoes e pontes encontradas.
    """
    n = grafo.n
    graus = [grafo.grau(v) for v in range(n)]
    conexo = n > 0 and len(componentes_conexas(grafo)) == 1
    articulacoes, pontes = articulacoes_e_pontes(grafo)
    grau_menor_que_2 = [v for v in range(n) if graus[v] < 2]
    grau_1 = [v for v in range(n) if graus[v] == 1]

    necessarias = [
        ("pelo menos 3 vertices", n >= 3),
        ("grafo conexo", conexo),
        ("todo vertice com grau >= 2", not grau_menor_que_2),
        ("nenhum vertice de articulacao", not articulacoes),
    ]
    dirac = n >= 3 and min(graus) >= n / 2
    ore = n >= 3 and _vale_ore(grafo, graus)
    suficientes = [("Dirac (grau minimo >= n/2)", dirac),
                   ("Ore (grau(u)+grau(v) >= n se u e v nao sao adjacentes)", ore)]

    ciclo = None
    falhas = [nome for (nome, ok) in necessarias if not ok]
    if falhas:
        classificacao = "nao hamiltoniano"
        motivo = "condicao necessaria violada: " + "; ".join(falhas)
    elif dirac or ore:
        classificacao = "hamiltoniano"
        motivo = "condicao suficiente satisfeita: " + ("Dirac" if dirac else "Ore")
    elif n <= LIMITE_BUSCA_HAMILTONIANA:
        ciclo = _ciclo_hamiltoniano_exaustivo(grafo)
        classificacao = "hamiltoniano" if ciclo else "nao hamiltoniano"
        motivo = "busca exaustiva " + ("encontrou um ciclo" if ciclo else "nao encontrou ciclo")
    else:
        classificacao = "inconclusivo"
        motivo = ("as condicoes necessarias valem, mas nenhuma suficiente; "
                  "a busca exaustiva e inviavel para este tamanho")

    if not conexo:
        percurso = "nao admite percurso hamiltoniano: o grafo e desconexo"
    elif len(grau_1) > 2:
        percurso = (f"nao admite percurso hamiltoniano: {len(grau_1)} vertices "
                    "de grau 1, e no maximo dois podem ser pontas do percurso")
    elif classificacao == "hamiltoniano":
        percurso = "admite percurso hamiltoniano (basta abrir o ciclo)"
    else:
        percurso = "inconclusivo pelas condicoes verificadas"

    return {
        "necessarias": necessarias,
        "suficientes": suficientes,
        "classificacao": classificacao,
        "motivo": motivo,
        "ciclo": ciclo,
        "percurso": percurso,
        "articulacoes": articulacoes,
        "pontes": pontes,
        "grau_1": grau_1,
    }


def _vale_ore(grafo, graus):
    """Confere a condicao de Ore para todos os pares nao adjacentes."""
    n = grafo.n
    for u in range(n):
        vizinhos = set(w for (w, _p) in grafo.vizinhos(u))
        for v in range(u + 1, n):
            if v not in vizinhos and graus[u] + graus[v] < n:
                return False
    return True


# 4. COLORACAO
def coloracao_welsh_powell(grafo):
    """
    Algoritmo de Welsh-Powell:
        1. ordena os vertices por grau decrescente;
        2. da a cor atual ao primeiro vertice sem cor da lista e, seguindo a
           lista, a todo vertice sem cor que nao seja vizinho de nenhum
           vertice que ja recebeu essa cor;
        3. passa para a proxima cor e repete ate todos terem cor.

    Devolve a lista 'cor', com a cor (0, 1, 2, ...) de cada vertice.
    O numero de cores usado e um limite superior do numero cromatico.
    """
    ordem = sorted(range(grafo.n), key=lambda v: (-grafo.grau(v), v))
    cor = [-1] * grafo.n
    cor_atual = 0

    for inicio in ordem:
        if cor[inicio] != -1:
            continue
        com_esta_cor = []
        for v in ordem:
            if cor[v] != -1:
                continue
            vizinhos = set(w for (w, _p) in grafo.vizinhos(v))
            if not any(u in vizinhos for u in com_esta_cor):
                cor[v] = cor_atual
                com_esta_cor.append(v)
        cor_atual += 1

    return cor


def coloracao_valida(grafo, cor):
    """Confere que nenhuma aresta liga dois vertices da mesma cor."""
    return all(cor[v] != cor[w] for (v, w, _p) in grafo.arestas())


def maior_clique(grafo):
    """
    Maior clique do grafo pelo algoritmo de Bron-Kerbosch com pivo.
    O tamanho da maior clique e um limite inferior do numero cromatico:
    os vertices de uma clique precisam, todos, de cores diferentes.
    Devolve a clique como lista ordenada de vertices.
    """
    adj = [set(w for (w, _p) in grafo.vizinhos(v)) for v in range(grafo.n)]
    melhor = []

    def expandir(r, p, x):
        nonlocal melhor
        if not p and not x:
            if len(r) > len(melhor):
                melhor = sorted(r)
            return
        if len(r) + len(p) <= len(melhor):
            return  # poda: nem levando todo P supera a melhor ja achada
        pivo = max(p | x, key=lambda u: len(adj[u] & p))
        for v in list(p - adj[pivo]):
            expandir(r | {v}, p & adj[v], x & adj[v])
            p = p - {v}
            x = x | {v}

    expandir(set(), set(range(grafo.n)), set())
    return melhor


def analise_coloracao(grafo):
    """
    Junta Welsh-Powell e maior clique. Devolve um dicionario com a cor de
    cada vertice, o numero de cores, as classes de cor (listas de
    vertices), a maior clique, os limites do numero cromatico, se o valor e
    exato, se a coloracao e valida e se o grafo e bipartido (2 cores).
    """
    cor = coloracao_welsh_powell(grafo)
    num_cores = max(cor) + 1 if cor else 0
    classes = [[v for v in range(grafo.n) if cor[v] == c] for c in range(num_cores)]
    clique = maior_clique(grafo) if grafo.n else []
    grau_maximo = max((grafo.grau(v) for v in range(grafo.n)), default=0)

    return {
        "cor": cor,
        "num_cores": num_cores,
        "classes": classes,
        "clique": clique,
        "limite_inferior": len(clique),
        "limite_superior": num_cores,
        "limite_brooks": grau_maximo + 1,
        "exato": len(clique) == num_cores,
        "valida": coloracao_valida(grafo, cor),
        "bipartido": num_cores <= 2,
    }
