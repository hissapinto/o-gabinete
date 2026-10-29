"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/prototipo/exportar_dados.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Gera os JSONs estaticos que o prototipo de alta fidelidade le, no mesmo
    formato que os endpoints da API devolvem:

        dados/anos.json                          <- GET /anos
        dados/anos/<ano>/grafo.json              <- GET /anos/<ano>/grafo
        dados/anos/<ano>/deputados/<id>.json     <- GET /anos/<ano>/deputados/<id>

    Unico acrescimo ao contrato: cada no do grafo ganha x e y, o layout
    calculado aqui com o NetworkX, para o navegador abrir o grafo pronto e
    sempre com o mesmo desenho.

    Duas fontes, nesta ordem:
      1. a API rodando localmente (docker compose up): as respostas sao
         salvas como vieram, o que garante o contrato;
      2. se a API nao responder, dados/grafo.txt, imitando os endpoints. Como
         o grafo.txt so tem o indice do vertice, o id e a foto de cada
         deputado vem da API de Dados Abertos da Camara, casando por nome+UF.
         Quem nao casar recebe um id sintetico e fica sem foto, e entra no
         relatorio_casamento.txt.

    Uso:
        pip install -r requirements.txt
        python exportar_dados.py                  # limiar 75, sem corte extra
        python exportar_dados.py --limiar 90 --k 3

Historico de alteracoes:
    29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

import networkx as nx
import numpy as np

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parent.parent
GRAFO_TXT = RAIZ / 'dados' / 'grafo.txt'
SAIDA = PASTA / 'dados'
RELATORIO = PASTA / 'relatorio_casamento.txt'

API_LOCAL = 'http://localhost:8000'
# grafo.txt e gerado para um ano so: ANO_REFERENCIA em pipeline/coleta.py
ANO_DO_GRAFO_TXT = 2024
# o mesmo corte do pipeline (CONCORDANCIA_MINIMA em pipeline/gerar_grafo.py)
LIMIAR_PADRAO = 75
# quantos mais similares a ficha traz no fallback
LIMITE_SIMILARES = 5

CAMARA = 'https://dadosabertos.camara.leg.br/api/v2/deputados'
LEGISLATURA = 57  # 2023-2027, cobre o ano do grafo.txt
ID_SINTETICO = 9_000_000  # somado ao indice do vertice de quem nao casou

# Layout, em pixels do Cytoscape (o no do prototipo mede 26): distancia
# minima entre centros de nos, espaco medio de cada deputado no desenho e
# folga entre componentes desconexos.
DISTANCIA_MINIMA = 34
AREA_POR_NO = 50 ** 2
FOLGA_COMPONENTES = 80
# ForceAtlas2. O modo linlog junta cada bloco sem achatar o desenho numa
# faixa (proporcao ~2:1 em vez de ~5:1) e mantem os blocos separados.
ITERACOES_LAYOUT = 1500
GRAVIDADE = 1.0
# Partido que fica do lado esquerdo do desenho, so para fixar o sentido.
PARTIDO_A_ESQUERDA = 'PT'


# --- leitura de URLs --------------------------------------------------------

def baixar_json(url, tempo=10):
    """GET em url devolvendo o JSON. Erros de rede sobem para quem chama."""
    pedido = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(pedido, timeout=tempo) as resposta:
        return json.load(resposta)


def api_no_ar(base):
    try:
        return baixar_json(f'{base}/health', tempo=3).get('status') == 'ok'
    except (urllib.error.URLError, OSError, ValueError):
        return False


# --- utilitarios ------------------------------------------------------------

def normalizar(texto):
    """Sem acento, sem pontuacao repetida e em minusculas, para casar nomes."""
    sem_acento = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', sem_acento).strip().casefold()


def gravar(caminho, conteudo):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, separators=(',', ':'))


# --- recortes de arestas ----------------------------------------------------

def filtrar_arestas(arestas, limiar, k, nomes):
    """
    Aplica o limiar minimo de similaridade (UC01, extensao 3a) e, se k vier,
    guarda so os k vizinhos mais parecidos de cada deputado, como o pipeline
    faz. Empate de percentual desempata pelo nome do vizinho.
    """
    arestas = [a for a in arestas if a['percentual'] >= limiar]
    if not k:
        return arestas

    por_no = {}
    for aresta in arestas:
        por_no.setdefault(aresta['deputado_a'], []).append((aresta, aresta['deputado_b']))
        por_no.setdefault(aresta['deputado_b'], []).append((aresta, aresta['deputado_a']))

    mantidas = set()
    for vizinhos in por_no.values():
        vizinhos.sort(key=lambda par: (-par[0]['percentual'], normalizar(nomes[par[1]])))
        for aresta, _ in vizinhos[:k]:
            mantidas.add((aresta['deputado_a'], aresta['deputado_b']))
    return [a for a in arestas if (a['deputado_a'], a['deputado_b']) in mantidas]


# --- layout -----------------------------------------------------------------

def calcular_layout(nos, arestas):
    """
    Posicoes x/y de cada no. Cada componente conexo e desenhado com o
    ForceAtlas2 do NetworkX (semente fixa: o mesmo grafo sempre sai com o
    mesmo desenho), deitado no eixo de maior espalhamento, que cabe melhor
    numa tela larga, e com os nos afastados ate nao se sobreporem. Os
    componentes menores sao encaixados no espaco livre perto do maior, em
    vez de soltos longe, o que encolheria o grafo ao enquadrar a tela toda.
    A escala e a mesma nos dois eixos: a proporcao do ForceAtlas2 e mantida.
    """
    grafo = nx.Graph()
    grafo.add_nodes_from(no['deputado_id'] for no in nos)
    if arestas:
        # o peso entra normalizado pelo intervalo real dos percentuais, que
        # ficam concentrados perto de 100
        pesos = [a['percentual'] for a in arestas]
        menor, maior = min(pesos), max(pesos)
        faixa = (maior - menor) or 1
        for aresta in arestas:
            relativo = (aresta['percentual'] - menor) / faixa
            grafo.add_edge(aresta['deputado_a'], aresta['deputado_b'], weight=0.2 + relativo)

    if grafo.number_of_nodes() == 0:
        return {}

    partidos = {no['deputado_id']: no['sigla_partido'] for no in nos}
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
            componente, weight='weight', seed=42, max_iter=ITERACOES_LAYOUT,
            gravity=GRAVIDADE, linlog=True, scaling_ratio=2.0)
    pontos = np.array([posicoes[i] for i in ids], dtype=float)
    pontos -= pontos.mean(axis=0)

    # deita o desenho: o eixo de maior variancia vira o horizontal
    _, _, eixos = np.linalg.svd(pontos, full_matrices=False)
    pontos = pontos @ eixos.T
    # Sentido fixo, para o desenho nao espelhar de um ano para o outro: o
    # PARTIDO_A_ESQUERDA, quando esta no componente, fica do lado esquerdo.
    lado = [x for i, (x, _) in zip(ids, pontos) if partidos[i] == PARTIDO_A_ESQUERDA]
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
    gerador = np.random.default_rng(42)
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
    aumenta a caixa do desenho, e, no empate, a mais perto do centro dela.
    Assim ele ocupa um vao do desenho em vez de abrir espaco vazio.
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


def montar_grafo_com_layout(ano, nos, arestas, limiar, k):
    """Resposta de GET /anos/<ano>/grafo, com o recorte de arestas e x/y nos nos."""
    nomes = {no['deputado_id']: no['nome'] for no in nos}
    arestas = filtrar_arestas(arestas, limiar, k, nomes)
    posicoes = calcular_layout(nos, arestas)
    nos_com_xy = []
    for no in nos:
        x, y = posicoes.get(no['deputado_id'], (0.0, 0.0))
        nos_com_xy.append({**no, 'x': x, 'y': y})
    return {'ano': ano, 'nos': nos_com_xy, 'arestas': arestas}


# --- fonte 1: a API ---------------------------------------------------------

def exportar_da_api(base, limiar, k):
    anos_ok = []
    for item in baixar_json(f'{base}/anos')['anos']:
        ano = item['ano']
        try:
            grafo = baixar_json(f'{base}/anos/{ano}/grafo')
        except urllib.error.HTTPError as erro:
            print(f'  {ano}: grafo indisponivel ({erro.code}), pulado')
            continue

        resposta = montar_grafo_com_layout(ano, grafo['nos'], grafo['arestas'], limiar, k)
        pasta_ano = SAIDA / 'anos' / str(ano)
        shutil.rmtree(pasta_ano, ignore_errors=True)
        gravar(pasta_ano / 'grafo.json', resposta)

        for no in grafo['nos']:
            ficha = baixar_json(
                f"{base}/anos/{ano}/deputados/{no['deputado_id']}?limite={LIMITE_SIMILARES}")
            gravar(pasta_ano / 'deputados' / f"{no['deputado_id']}.json", ficha)

        print(f"  {ano}: {len(resposta['nos'])} deputados, {len(resposta['arestas'])} arestas")
        anos_ok.append({'ano': ano})
    return anos_ok


# --- fonte 2: dados/grafo.txt -----------------------------------------------

ROTULO = re.compile(r'^(?P<nome>.*) \((?P<partido>[^()]+)-(?P<uf>[A-Z]{2})\)$')


def ler_grafo_txt(caminho):
    """
    Le o grafo.txt (tipo 2, formato do enunciado). Devolve a lista de vertices
    {indice, nome, sigla_partido, sigla_uf} e as arestas (v, w, peso).
    """
    linhas = caminho.read_text(encoding='utf-8').splitlines()
    total_vertices = int(linhas[1])
    vertices = []
    for linha in linhas[2:2 + total_vertices]:
        indice, rotulo = linha.split(' ', 1)
        casamento = ROTULO.match(rotulo.strip().strip('"'))
        vertices.append({
            'indice': int(indice),
            'nome': casamento['nome'],
            'sigla_partido': casamento['partido'],
            'sigla_uf': casamento['uf'],
        })

    inicio = 2 + total_vertices
    total_arestas = int(linhas[inicio])
    arestas = []
    for linha in linhas[inicio + 1:inicio + 1 + total_arestas]:
        v, w, peso = linha.split()
        arestas.append((int(v), int(w), int(peso)))
    return vertices, arestas


def baixar_deputados_camara():
    """Todos os deputados da legislatura, de todas as paginas da API da Camara."""
    deputados = []
    url = f'{CAMARA}?idLegislatura={LEGISLATURA}&itens=100&ordem=ASC&ordenarPor=nome'
    while url:
        pagina = baixar_json(url, tempo=30)
        deputados.extend(pagina['dados'])
        url = next((link['href'] for link in pagina['links'] if link['rel'] == 'next'), None)
    return deputados


def casar_com_camara(vertices, deputados_camara):
    """
    Devolve {indice: (deputado_id, url_foto)} para quem casou por nome+UF e a
    lista de quem nao casou (nenhum ou mais de um candidato).
    """
    por_chave = {}
    for dep in deputados_camara:
        chave = (normalizar(dep['nome']), dep['siglaUf'])
        por_chave.setdefault(chave, {})[dep['id']] = dep['urlFoto']

    casados, sem_par = {}, []
    for vertice in vertices:
        candidatos = por_chave.get((normalizar(vertice['nome']), vertice['sigla_uf']), {})
        if len(candidatos) == 1:
            casados[vertice['indice']] = next(iter(candidatos.items()))
        else:
            sem_par.append((vertice, len(candidatos)))
    return casados, sem_par


def gravar_relatorio(sem_par, total, fonte_ok):
    with open(RELATORIO, 'w', encoding='utf-8') as arquivo:
        arquivo.write('Casamento por nome+UF entre dados/grafo.txt e a API de Dados Abertos da Camara\n')
        arquivo.write(f'(legislatura {LEGISLATURA}). Quem nao casou recebe id sintetico '
                      f'{ID_SINTETICO} + indice e aparece com avatar de iniciais.\n\n')
        if not fonte_ok:
            arquivo.write('A API da Camara nao respondeu: nenhum deputado casou.\n')
        arquivo.write(f'Casaram: {total - len(sem_par)} de {total}\n')
        arquivo.write(f'Nao casaram: {len(sem_par)}\n\n')
        for vertice, candidatos in sem_par:
            motivo = 'nenhum candidato' if candidatos == 0 else f'{candidatos} candidatos'
            arquivo.write(f"  [{vertice['indice']}] {vertice['nome']} "
                          f"({vertice['sigla_partido']}-{vertice['sigla_uf']}): {motivo}\n")


def exportar_do_grafo_txt(ano, limiar, k, consultar_camara):
    vertices, arestas_txt = ler_grafo_txt(GRAFO_TXT)

    deputados_camara, fonte_ok = [], False
    if consultar_camara:
        try:
            deputados_camara = baixar_deputados_camara()
            fonte_ok = True
        except (urllib.error.URLError, OSError, ValueError) as erro:
            print(f'  aviso: API da Camara indisponivel ({erro}); todos ficam com id sintetico')
    casados, sem_par = casar_com_camara(vertices, deputados_camara)
    gravar_relatorio(sem_par, len(vertices), fonte_ok)

    ids, fotos = {}, {}
    for vertice in vertices:
        indice = vertice['indice']
        ids[indice], fotos[indice] = casados.get(indice, (ID_SINTETICO + indice, None))

    # nos como o listar_nos da API: sem url_foto, em ordem de nome
    nos = [{
        'deputado_id': ids[v['indice']],
        'nome': v['nome'],
        'sigla_partido': v['sigla_partido'],
        'sigla_uf': v['sigla_uf'],
    } for v in vertices]
    nos.sort(key=lambda no: normalizar(no['nome']))

    # o banco guarda o par com o menor id em deputado_a; o mesmo vale aqui
    arestas = []
    for v, w, peso in arestas_txt:
        a, b = sorted((ids[v], ids[w]))
        arestas.append({'deputado_a': a, 'deputado_b': b, 'percentual': float(peso)})
    arestas.sort(key=lambda aresta: (aresta['deputado_a'], aresta['deputado_b']))

    resposta = montar_grafo_com_layout(ano, nos, arestas, limiar, k)
    pasta_ano = SAIDA / 'anos' / str(ano)
    shutil.rmtree(pasta_ano, ignore_errors=True)
    gravar(pasta_ano / 'grafo.json', resposta)

    # Ficha de cada um. Os mais similares saem de todas as arestas do
    # grafo.txt, antes do limiar e do k, como na API, que le a concordancia
    # completa e nao so as arestas desenhadas.
    por_id = {no['deputado_id']: no for no in nos}
    vizinhos = {no_id: [] for no_id in por_id}
    for aresta in arestas:
        vizinhos[aresta['deputado_a']].append((aresta['deputado_b'], aresta['percentual']))
        vizinhos[aresta['deputado_b']].append((aresta['deputado_a'], aresta['percentual']))

    indice_por_id = {ids[v['indice']]: v['indice'] for v in vertices}
    for no_id, no in por_id.items():
        lista = sorted(vizinhos[no_id], key=lambda par: (-par[1], normalizar(por_id[par[0]]['nome'])))
        gravar(pasta_ano / 'deputados' / f'{no_id}.json', {
            'ano': ano,
            'deputado': {**no, 'url_foto': fotos[indice_por_id[no_id]]},
            'mais_similares': [{
                'deputado_id': outro,
                'nome': por_id[outro]['nome'],
                'sigla_partido': por_id[outro]['sigla_partido'],
                'percentual': percentual,
                'votacoes_em_comum': None,  # o grafo.txt nao guarda esse numero
            } for outro, percentual in lista[:LIMITE_SIMILARES]],
        })

    print(f"  {ano}: {len(resposta['nos'])} deputados, {len(resposta['arestas'])} arestas")
    print(f'  ids da Camara: {len(casados)} casaram, {len(sem_par)} nao casaram '
          f'(ver {RELATORIO.relative_to(RAIZ)})')
    return [{'ano': ano}]


# --- principal --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split('Sintese:')[0].strip())
    parser.add_argument('--api', default=API_LOCAL, help=f'URL da API (padrao {API_LOCAL})')
    parser.add_argument('--limiar', type=float, default=LIMIAR_PADRAO,
                        help=f'similaridade minima, em %%, para a aresta entrar (padrao {LIMIAR_PADRAO})')
    parser.add_argument('--k', type=int, default=None,
                        help='guarda so os k vizinhos mais parecidos de cada deputado (padrao: sem corte)')
    parser.add_argument('--sem-camara', action='store_true',
                        help='no fallback, nao consulta a API da Camara (ids sinteticos, sem fotos)')
    args = parser.parse_args()

    if api_no_ar(args.api):
        print(f'Fonte: API em {args.api}')
        anos = exportar_da_api(args.api, args.limiar, args.k)
    else:
        print(f'API em {args.api} fora do ar. Fonte: {GRAFO_TXT.relative_to(RAIZ)}')
        anos = exportar_do_grafo_txt(ANO_DO_GRAFO_TXT, args.limiar, args.k, not args.sem_camara)

    if not anos:
        sys.exit('Nenhum ano exportado.')
    gravar(SAIDA / 'anos.json', {'anos': anos})
    print(f"Anos exportados: {', '.join(str(a['ano']) for a in anos)}")


if __name__ == '__main__':
    main()
