"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/layout.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Posicao x/y de cada vertice do grafo, para a interface web abrir o grafo
    ja desenhado e sempre com o mesmo desenho. A carga.py grava o resultado
    em app.posicao, e a API devolve x/y em cada no de GET /anos/{ano}/grafo.

    Mesma logica e mesmos parametros do web/prototipo/exportar_dados.py, que
    desenhou o prototipo de IHC: ForceAtlas2 do NetworkX (modo linlog,
    semente fixa), cada componente deitado no eixo de maior espalhamento, PT
    a esquerda, escala unica nos dois eixos, nos afastados ate nao se
    sobreporem e componentes menores encaixados no vao livre do desenho.

    O NetworkX fica so aqui, no pipeline: o nucleo em grafos/ continua sem
    biblioteca externa de grafos (RNF03).
"""

import networkx as nx
import numpy as np

# Em pixels do Cytoscape (o no da interface mede 26): distancia minima entre
# centros de nos, espaco medio de cada deputado no desenho e folga entre
# componentes desconexos.
DISTANCIA_MINIMA = 34
AREA_POR_NO = 50 ** 2
FOLGA_COMPONENTES = 80
# ForceAtlas2. O modo linlog junta cada bloco sem achatar o desenho numa
# faixa (proporcao ~2:1 em vez de ~5:1) e mantem os blocos separados.
ITERACOES_LAYOUT = 1500
GRAVIDADE = 1.0
SEMENTE = 42
# Partido que fica do lado esquerdo do desenho, so para fixar o sentido.
PARTIDO_A_ESQUERDA = 'PT'


def calcular_layout(ids, partidos, arestas):
    """
    Posicoes de cada vertice: {deputado_id: (x, y)}, com uma casa decimal.

    ids       deputado_ids na ordem dos vertices (a mesma do grafo.txt). A
              ordem importa: o ForceAtlas2 sorteia as posicoes iniciais
              nessa ordem.
    partidos  {deputado_id: sigla_partido}, para fixar o PT a esquerda.
    arestas   {(deputado_a, deputado_b): peso}, peso inteiro de 0 a 100.

    Todo id recebe posicao, inclusive vertice isolado.
    """
    grafo = nx.Graph()
    grafo.add_nodes_from(ids)
    if arestas:
        # o peso entra normalizado pelo intervalo real, porque os pesos
        # ficam concentrados perto de 100
        menor, maior = min(arestas.values()), max(arestas.values())
        faixa = (maior - menor) or 1
        for (a, b), peso in sorted(arestas.items()):
            grafo.add_edge(a, b, weight=0.2 + (peso - menor) / faixa)

    if grafo.number_of_nodes() == 0:
        return {}

    componentes = sorted(nx.connected_components(grafo), key=lambda c: (-len(c), min(c)))
    blocos = [desenhar_componente(grafo.subgraph(c), partidos) for c in componentes]
    return encaixar_componentes(blocos)


def desenhar_componente(componente, partidos):
    """Posicoes de um componente conexo, centradas em (0, 0): {id: array([x, y])}."""
    ids = list(componente.nodes)
    if len(ids) == 1:
        return {ids[0]: np.zeros(2)}

    # o linlog do NetworkX divide pela distancia de cada no a si mesmo (zero)
    # e descarta o resultado; o aviso de numpy que isso gera e so ruido
    with np.errstate(divide='ignore', invalid='ignore'):
        posicoes = nx.forceatlas2_layout(
            componente, weight='weight', seed=SEMENTE, max_iter=ITERACOES_LAYOUT,
            gravity=GRAVIDADE, linlog=True, scaling_ratio=2.0)
    pontos = np.array([posicoes[i] for i in ids], dtype=float)
    pontos -= pontos.mean(axis=0)

    # deita o desenho: o eixo de maior variancia vira o horizontal
    _, _, eixos = np.linalg.svd(pontos, full_matrices=False)
    pontos = pontos @ eixos.T
    # Sentido fixo, para o desenho nao espelhar de um ano para o outro: o
    # PARTIDO_A_ESQUERDA, quando esta no componente, fica do lado esquerdo.
    lado = [x for i, (x, _) in zip(ids, pontos) if partidos.get(i) == PARTIDO_A_ESQUERDA]
    if lado and np.mean(lado) > 0:
        pontos[:, 0] *= -1

    # escala unica (x e y), para cada no ter em media AREA_POR_NO de espaco
    largura, altura = np.ptp(pontos, axis=0)
    area = max(largura * altura, 1e-9)
    pontos *= np.sqrt(len(ids) * AREA_POR_NO / area)

    pontos = afastar_sobrepostos(pontos)
    return dict(zip(ids, pontos))


def afastar_sobrepostos(pontos, iteracoes=400):
    """Empurra os pares mais proximos que DISTANCIA_MINIMA ate se desgrudarem."""
    gerador = np.random.default_rng(SEMENTE)
    pontos = pontos + gerador.normal(0, 0.01, pontos.shape)  # desfaz pontos identicos
    for _ in range(iteracoes):
        diferenca = pontos[:, None, :] - pontos[None, :, :]
        distancia = np.hypot(diferenca[..., 0], diferenca[..., 1])
        np.fill_diagonal(distancia, np.inf)
        falta = np.clip(DISTANCIA_MINIMA - distancia, 0, None)
        if falta.max() < 0.5:
            break
        direcao = diferenca / distancia[..., None]
        pontos = pontos + (direcao * (falta / 2)[..., None]).sum(axis=1) * 0.5
    return pontos


def encaixar_componentes(blocos, passo=20):
    """
    O maior componente fica onde esta; cada um dos menores vai para a posicao
    livre (a pelo menos FOLGA_COMPONENTES de qualquer no ja posto) que menos
    aumenta a caixa do desenho e, no empate, a mais perto do centro dela.
    Assim ele ocupa um vao do desenho em vez de abrir espaco vazio.
    Devolve {id: (x, y)} com o desenho todo centrado em (0, 0).
    """
    final = dict(blocos[0])
    for bloco in blocos[1:]:
        ocupados = np.array(list(final.values()))
        pontos = np.array(list(bloco.values()))
        pontos -= (pontos.min(axis=0) + pontos.max(axis=0)) / 2
        meia = np.ptp(pontos, axis=0) / 2 + FOLGA_COMPONENTES
        baixo, alto = ocupados.min(axis=0) - meia, ocupados.max(axis=0) + meia
        centro = (ocupados.min(axis=0) + ocupados.max(axis=0)) / 2

        melhor = None
        for x in np.arange(baixo[0], alto[0] + passo, passo):
            for y in np.arange(baixo[1], alto[1] + passo, passo):
                posto = pontos + (x, y)
                distancia = np.hypot(*(posto[:, None, :] - ocupados[None, :, :]).transpose(2, 0, 1))
                if distancia.min() < FOLGA_COMPONENTES:
                    continue
                juntos = np.vstack([ocupados, posto])
                area = np.prod(np.ptp(juntos, axis=0))
                chave = (round(area, -3), np.hypot(x - centro[0], y - centro[1]))
                if melhor is None or chave < melhor[0]:
                    melhor = (chave, (x, y))

        deslocamento = np.array(melhor[1])
        for no, ponto in zip(bloco, pontos):
            final[no] = ponto + deslocamento

    pontos = np.array(list(final.values()))
    centro = (pontos.min(axis=0) + pontos.max(axis=0)) / 2
    return {no: (round(float(x), 1), round(float(y), 1)) for no, (x, y) in
            ((no, ponto - centro) for no, ponto in final.items())}
