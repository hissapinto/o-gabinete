"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: grafos/apresentacao/menu.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Camada de apresentacao. Exibe o menu de opcoes no terminal, le a escolha
    do usuario, chama a camada de negocio ou de persistencia e formata o
    resultado. Nao contem regra de negocio nem conhece o formato do arquivo.

Historico de alteracoes:
    24/09/2026 - Grupo - Criacao do menu com as dez opcoes do enunciado.
    18/10/2026 - Isabela - Caminho do cabecalho atualizado apos a reorganizacao das pastas.
    19/11/2026 - Kaique - Parte 3: opcao (j) de deteccao de blocos de votacao
                          pela arvore geradora maxima, opcoes (k) a (n) com as
                          caracteristicas do grafo (grau, Euler, Hamilton e
                          coloracao) e encerramento movido para a opcao (o).
"""

import persistencia
from grafo import GrafoPonderadoND
import logica_grafos
import blocos as blocos_votacao
import caracteristicas

LARGURA = 66
POR_PAGINA = 20  # vertices por pagina na opcao (h)
AMOSTRA = 10     # linhas exibidas no resumo da opcao (g)

# Parametros padrao da opcao (j). Com 3 blocos e minimo de 10 deputados por
# bloco a modularidade e a maior entre as combinacoes testadas; acima de 3
# blocos os cortes caem em arestas de 100% e passam a depender de empates.
BLOCOS_PADRAO = 3
TAMANHO_MINIMO_PADRAO = 10


# ESTADO DA APLICACAO
class Aplicacao:
    """Guarda o grafo carregado e se existem alteracoes ainda nao gravadas."""

    def __init__(self):
        self.grafo = GrafoPonderadoND(0)
        self.caminho = persistencia.CAMINHO_PADRAO
        self.alterado = False
        self.carregado = False


# APRESENTACAO
def titulo():
    print("\n" + "=" * LARGURA)
    print("  O GABINETE".center(LARGURA))
    print("  Mapa de Similaridade Politica entre Deputados Federais".center(LARGURA))
    print("  Deteccao de Blocos de Votacao na Camara dos Deputados".center(LARGURA))
    print("=" * LARGURA)


def cabecalho(texto):
    print("\n" + "-" * LARGURA)
    print(f"  {texto}")
    print("-" * LARGURA)


def situacao(app):
    if not app.carregado:
        return "nenhum grafo carregado"
    marca = " (com alteracoes nao gravadas)" if app.alterado else ""
    return f"{app.grafo.n} vertices, {app.grafo.m} arestas{marca}"


def mostrar_menu(app):
    titulo()
    print(f"  Estado: {situacao(app)}")
    print(f"  Arquivo: {app.caminho}")
    print("-" * LARGURA)
    print("""
  [a] Ler dados do arquivo grafo.txt
  [b] Gravar dados no arquivo grafo.txt
  [c] Inserir vertice
  [d] Inserir aresta
  [e] Remover vertice
  [f] Remover aresta
  [g] Mostrar conteudo do arquivo
  [h] Mostrar grafo
  [i] Apresentar a conexidade do grafo

  SOLUCAO DO PROBLEMA
  [j] Detectar blocos de votacao (arvore geradora maxima)

  CARACTERISTICAS DO GRAFO
  [k] Grau dos vertices
  [l] Grafo euleriano
  [m] Grafo hamiltoniano (e deputados-ponte)
  [n] Coloracao do grafo

  [o] Encerrar a aplicacao
""")
    print("=" * LARGURA)


# ENTRADA DE DADOS
def ler_inteiro(mensagem):
    """Le um inteiro do teclado. Devolve None se a entrada for invalida."""
    try:
        return int(input(mensagem).strip())
    except ValueError:
        print("\n  Valor invalido: informe um numero inteiro.")
        return None


def exige_grafo(app):
    """Confere se ha grafo carregado antes de operar sobre ele."""
    if not app.carregado:
        print("\n  Nenhum grafo carregado. Use a opcao [a] primeiro.")
        return False
    return True


def descreve(grafo, v):
    """Monta 'indice (rotulo)' para as mensagens do menu."""
    return f"{v} ({grafo.rotulo(v)})"


# OPCOES DO MENU
def opcao_a_ler(app):
    """(a) Le o arquivo grafo.txt e monta a lista de adjacencia."""
    cabecalho("(a) LER DADOS DO ARQUIVO")

    if app.alterado:
        resposta = input("  Ha alteracoes nao gravadas. Descartar? (s/n): ")
        if resposta.strip().lower() != "s":
            print("\n  Leitura cancelada.")
            return

    caminho = input(f"  Caminho [{app.caminho}]: ").strip() or app.caminho

    try:
        app.grafo = persistencia.ler(caminho)
    except persistencia.ErroDeArquivo as erro:
        print(f"\n  Nao foi possivel ler o arquivo: {erro}")
        return

    app.caminho = caminho
    app.carregado = True
    app.alterado = False
    print(f"\n  Grafo carregado com sucesso de '{caminho}'.")
    print(f"  {app.grafo.n} vertices e {app.grafo.m} arestas.")


def opcao_b_gravar(app):
    """(b) Grava o grafo da memoria no arquivo, no formato da leitura."""
    cabecalho("(b) GRAVAR DADOS NO ARQUIVO")

    if not exige_grafo(app):
        return

    caminho = input(f"  Caminho [{app.caminho}]: ").strip() or app.caminho

    try:
        total = persistencia.gravar(app.grafo, caminho)
    except OSError as erro:
        print(f"\n  Nao foi possivel gravar o arquivo: {erro}")
        return

    app.caminho = caminho
    app.alterado = False
    print(f"\n  Grafo gravado em '{caminho}'.")
    print(f"  {app.grafo.n} vertices e {total} arestas.")


def opcao_c_inserir_vertice(app):
    """(c) Insere um novo vertice com o seu rotulo."""
    cabecalho("(c) INSERIR VERTICE")

    if not exige_grafo(app):
        return

    rotulo = input("  Rotulo do vertice (nome do deputado): ").strip()
    if not rotulo:
        print("\n  O rotulo nao pode ficar vazio.")
        return

    v = app.grafo.insereV(rotulo)
    app.alterado = True
    print(f"\n  Vertice inserido: {descreve(app.grafo, v)}")
    print(f"  O grafo passa a ter {app.grafo.n} vertices.")


def opcao_d_inserir_aresta(app):
    """(d) Insere uma aresta com peso entre dois vertices."""
    cabecalho("(d) INSERIR ARESTA")

    if not exige_grafo(app):
        return

    v = ler_inteiro("  Vertice de origem: ")
    if v is None:
        return
    w = ler_inteiro("  Vertice de destino: ")
    if w is None:
        return
    peso = ler_inteiro("  Peso (similaridade de 0 a 100): ")
    if peso is None:
        return

    if not app.grafo.existeV(v) or not app.grafo.existeV(w):
        print(f"\n  Vertice inexistente. Use indices entre 0 e {app.grafo.n - 1}.")
        return
    if v == w:
        print("\n  Nao e possivel ligar um vertice a ele mesmo.")
        return
    if not 0 <= peso <= 100:
        print("\n  O peso deve estar entre 0 e 100.")
        return

    existia = app.grafo.existeA(v, w)
    app.grafo.insereA(v, w, peso)
    app.alterado = True

    acao = "atualizada" if existia else "inserida"
    print(f"\n  Aresta {acao}: {descreve(app.grafo, v)} -- "
          f"{descreve(app.grafo, w)}  peso {peso}")


def opcao_e_remover_vertice(app):
    """(e) Remove um vertice e todas as arestas incidentes a ele."""
    cabecalho("(e) REMOVER VERTICE")

    if not exige_grafo(app):
        return

    v = ler_inteiro("  Vertice a remover: ")
    if v is None:
        return
    if not app.grafo.existeV(v):
        print(f"\n  Vertice inexistente. Use indices entre 0 e {app.grafo.n - 1}.")
        return

    nome = app.grafo.rotulo(v)
    incidentes = app.grafo.grau(v)

    resposta = input(f"  Remover {v} ({nome}) e {incidentes} aresta(s)? (s/n): ")
    if resposta.strip().lower() != "s":
        print("\n  Remocao cancelada.")
        return

    app.grafo.removeV(v)
    app.alterado = True
    print(f"\n  Vertice {v} ({nome}) removido, junto com {incidentes} aresta(s).")
    print("  Os vertices seguintes foram renumerados.")
    print(f"  O grafo passa a ter {app.grafo.n} vertices e {app.grafo.m} arestas.")


def opcao_f_remover_aresta(app):
    """(f) Remove uma aresta entre dois vertices."""
    cabecalho("(f) REMOVER ARESTA")

    if not exige_grafo(app):
        return

    v = ler_inteiro("  Vertice de origem: ")
    if v is None:
        return
    w = ler_inteiro("  Vertice de destino: ")
    if w is None:
        return

    if not app.grafo.existeA(v, w):
        print("\n  Nao existe aresta entre esses vertices.")
        return

    peso = app.grafo.peso(v, w)
    app.grafo.removeA(v, w)
    app.alterado = True
    print(f"\n  Aresta removida: {descreve(app.grafo, v)} -- "
          f"{descreve(app.grafo, w)}  (peso {peso})")
    print(f"  O grafo passa a ter {app.grafo.m} arestas.")


def opcao_g_conteudo(app):
    """(g) Mostra o conteudo atual do arquivo em formato legivel."""
    cabecalho("(g) CONTEUDO DO ARQUIVO")

    try:
        bruto = persistencia.conteudo(app.caminho)
    except persistencia.ErroDeArquivo as erro:
        print(f"\n  Nao foi possivel ler o arquivo: {erro}")
        return

    linhas = [linha for linha in bruto.splitlines() if linha.strip()]
    if len(linhas) < 2:
        print("\n  O arquivo esta vazio ou incompleto.")
        return

    tipo = linhas[0].strip()
    n = int(linhas[1].split()[0])
    inicio_arestas = 2 + n
    m = int(linhas[inicio_arestas].split()[0]) if len(linhas) > inicio_arestas else 0

    print(f"\n  Arquivo ....: {app.caminho}")
    print(f"  Tipo .......: {tipo} (grafo nao orientado com peso na aresta)")
    print(f"  Vertices ...: {n}")
    print(f"  Arestas ....: {m}")

    if app.alterado:
        print("\n  Atencao: ha alteracoes em memoria ainda nao gravadas.")

    vertices = linhas[2:2 + n]
    arestas = linhas[inicio_arestas + 1:inicio_arestas + 1 + m]

    print("\n  VERTICES (indice e rotulo)")
    print("  " + "-" * (LARGURA - 4))
    _amostra(vertices, "  ")

    print("\n  ARESTAS (origem, destino e peso)")
    print("  " + "-" * (LARGURA - 4))
    _amostra(arestas, "  ")

    if len(vertices) + len(arestas) > 2 * AMOSTRA:
        resposta = input("\n  Ver o conteudo completo? (s/n): ")
        if resposta.strip().lower() == "s":
            print("\n  VERTICES")
            _paginar(vertices, "  ")
            print("\n  ARESTAS")
            _paginar(arestas, "  ")


def opcao_h_mostrar_grafo(app):
    """(h) Mostra o grafo como lista de adjacencia, com paginacao."""
    cabecalho("(h) MOSTRAR GRAFO (LISTA DE ADJACENCIA)")

    if not exige_grafo(app):
        return

    inicio = 0
    while inicio < app.grafo.n:
        fim = min(inicio + POR_PAGINA, app.grafo.n)
        app.grafo.show(inicio, fim)

        if fim >= app.grafo.n:
            break

        print(f"\n  Mostrando vertices {inicio} a {fim - 1} de {app.grafo.n - 1}.")
        resposta = input("  ENTER para continuar, 'q' para parar: ")
        if resposta.strip().lower() == "q":
            break
        inicio = fim


def opcao_i_conexidade(app):
    """(i) Apresenta a conexidade do grafo e suas componentes conexas."""
    cabecalho("(i) CONEXIDADE DO GRAFO")

    if not exige_grafo(app):
        return

    if app.grafo.n == 0:
        print("\n  O grafo nao possui vertices.")
        return

    componentes = logica_grafos.componentes_conexas(app.grafo)
    conexo = len(componentes) == 1

    print("\n  Tipo do grafo ....: nao orientado com peso na aresta (tipo 2)")
    print(f"  Classificacao ....: {'CONEXO' if conexo else 'DESCONEXO'}")
    print(f"  Componentes ......: {len(componentes)}")

    isolados = logica_grafos.vertices_isolados(app.grafo)
    print(f"  Vertices isolados : {len(isolados)}")

    print("\n  Observacao: o grafo reduzido e a classificacao C0/C1/C2/C3")
    print("  aplicam-se apenas a grafos orientados, e por isso nao se")
    print("  aplicam a esta modelagem.")

    print("\n  COMPONENTES CONEXAS")
    print("  " + "-" * (LARGURA - 4))

    for i, componente in enumerate(componentes, start=1):
        print(f"\n  Componente {i}: {len(componente)} vertice(s)")
        amostra = componente[:8]
        nomes = ", ".join(
            f"{v} ({app.grafo.rotulo(v)})" for v in amostra
        )
        print(f"    {nomes}", end="")
        if len(componente) > len(amostra):
            print(f", ... (+{len(componente) - len(amostra)})", end="")
        print()


def ler_inteiro_padrao(mensagem, padrao):
    """Le um inteiro; ENTER vazio devolve o padrao e entrada invalida, None."""
    texto = input(mensagem).strip()
    if texto == "":
        return padrao
    try:
        return int(texto)
    except ValueError:
        print("\n  Valor invalido: informe um numero inteiro.")
        return None


def _nomes(grafo, vertices, limite=6):
    """Monta 'indice (rotulo), ...' com no maximo 'limite' nomes."""
    texto = ", ".join(descreve(grafo, v) for v in vertices[:limite])
    if len(vertices) > limite:
        texto += f", ... (+{len(vertices) - limite})"
    return texto


def _barra(quantidade, maximo, largura=30):
    """Barra de texto proporcional, para os histogramas no terminal."""
    if maximo == 0:
        return ""
    return "#" * max(1, round(largura * quantidade / maximo)) if quantidade else ""


def opcao_j_blocos(app):
    """(j) Solucao: blocos de votacao pela arvore geradora maxima."""
    cabecalho("(j) DETECTAR BLOCOS DE VOTACAO (ARVORE GERADORA MAXIMA)")

    if not exige_grafo(app):
        return
    if app.grafo.m == 0:
        print("\n  O grafo nao possui arestas: nao ha afinidade para agrupar.")
        return

    num_blocos = ler_inteiro_padrao(
        f"  Quantidade de blocos [{BLOCOS_PADRAO}]: ", BLOCOS_PADRAO)
    if num_blocos is None:
        return
    minimo = ler_inteiro_padrao(
        f"  Tamanho minimo de cada bloco [{TAMANHO_MINIMO_PADRAO}]: ",
        TAMANHO_MINIMO_PADRAO)
    if minimo is None:
        return
    if not 1 <= num_blocos <= app.grafo.n:
        print(f"\n  A quantidade de blocos deve estar entre 1 e {app.grafo.n}.")
        return
    if not 1 <= minimo <= app.grafo.n:
        print(f"\n  O tamanho minimo deve estar entre 1 e {app.grafo.n}.")
        return

    grafo = app.grafo
    resultado = blocos_votacao.detectar_blocos(grafo, num_blocos, minimo)
    floresta = resultado["floresta"]
    cortes = resultado["cortes"]
    lista = resultado["blocos"]

    # 1. arvore geradora maxima
    total = blocos_votacao.peso_total(floresta)
    print("\n  1. FLORESTA GERADORA MAXIMA (KRUSKAL)")
    print("  " + "-" * (LARGURA - 4))
    print(f"  Arestas na floresta ...: {len(floresta)} de {grafo.m} "
          f"(n - componentes = {grafo.n} - {grafo.n - len(floresta)})")
    print(f"  Peso total ............: {total}")
    if floresta:
        print(f"  Concordancia media ....: {total / len(floresta):.1f}%")

    # 2. cortes
    print("\n  2. CORTES NAS ARESTAS MAIS FRACAS DA FLORESTA")
    print("  " + "-" * (LARGURA - 4))
    componentes = len(lista) - len(cortes)
    print(f"  Componentes conexas ja separadas: {componentes}")
    if not cortes:
        print("  Nenhum corte foi necessario ou possivel.")
    for (v, w, peso) in cortes:
        print(f"  corte ({peso}%): {descreve(grafo, v)} -- {descreve(grafo, w)}")
    significativos = resultado["significativos"]
    if significativos < num_blocos:
        print(f"\n  Atencao: so foi possivel formar {significativos} bloco(s) com pelo")
        print(f"  menos {minimo} deputado(s) cada.")

    # 3. blocos (os grupos menores que o minimo vem por ultimo, como avulsos)
    avulsos = len(lista) - significativos
    print(f"\n  3. BLOCOS DE VOTACAO ({significativos}"
          f"{f' + {avulsos} grupo(s) avulso(s)' if avulsos else ''})")
    print("  " + "-" * (LARGURA - 4))
    resumos = blocos_votacao.resumo_dos_blocos(grafo, lista)
    for i, (bloco, resumo) in enumerate(zip(lista, resumos), start=1):
        media = resumo["concordancia_media"]
        media_txt = f"{media:.1f}%" if media is not None else "-"
        partidos = ", ".join(
            f"{p} {q} ({100 * q / resumo['tamanho']:.0f}%)"
            for (p, q) in resumo["partidos"][:5]
        )
        tipo = "Bloco" if i <= significativos else "Grupo avulso"
        print(f"\n  {tipo} {i}: {resumo['tamanho']} deputado(s)")
        print(f"    Partidos ..........: {partidos}")
        print(f"    Arestas internas ..: {resumo['arestas_internas']} "
              f"(concordancia media {media_txt})")
        print(f"    Arestas para fora .: {resumo['arestas_externas']}")
        print(f"    Exemplos ..........: {_nomes(grafo, bloco, 4)}")

    # 4. qualidade
    q_blocos = blocos_votacao.modularidade(grafo, lista)
    q_partidos = blocos_votacao.modularidade(grafo, blocos_votacao.blocos_por_partido(grafo))
    print("\n  4. QUALIDADE DA DIVISAO (MODULARIDADE DE NEWMAN)")
    print("  " + "-" * (LARGURA - 4))
    print(f"  Blocos encontrados ....: Q = {q_blocos:.3f}")
    print(f"  Divisao por partido ...: Q = {q_partidos:.3f}")
    if q_blocos > q_partidos:
        print("  Os blocos explicam as arestas melhor que a filiacao partidaria.")
    else:
        print("  A filiacao partidaria explica as arestas tao bem ou melhor.")

    # membros de um bloco, sob demanda
    escolha = ler_inteiro_padrao(
        "\n  Ver todos os membros de um bloco? (numero ou ENTER): ", 0)
    if escolha and 1 <= escolha <= len(lista):
        linhas = [descreve(grafo, v) for v in lista[escolha - 1]]
        _paginar(linhas, "    ")

    resposta = input("\n  Mostrar a analise de sensibilidade? (s/n): ")
    if resposta.strip().lower() == "s":
        _mostrar_sensibilidade(grafo)


def _mostrar_sensibilidade(grafo):
    """Tabela da opcao (j) variando quantidade de blocos e tamanho minimo."""
    print("\n  SENSIBILIDADE AOS PARAMETROS")
    print("  " + "-" * (LARGURA - 4))
    print(f"  {'min':>4} {'pedido':>6} {'obtido':>6} {'Q':>7}   tamanhos")
    linhas = blocos_votacao.sensibilidade(grafo, range(2, 7), (5, 10, 20))
    for linha in linhas:
        tamanhos = ", ".join(str(t) for t in linha["tamanhos"])
        print(f"  {linha['tamanho_minimo']:>4} {linha['num_blocos']:>6} "
              f"{linha['obtidos']:>6} {linha['modularidade']:>7.3f}   {tamanhos}")


def opcao_k_grau(app):
    """(k) Caracteristica: grau dos vertices."""
    cabecalho("(k) GRAU DOS VERTICES")

    if not exige_grafo(app):
        return
    grafo = app.grafo
    resumo = caracteristicas.resumo_graus(grafo)
    if resumo is None:
        print("\n  O grafo nao possui vertices.")
        return

    print(f"\n  Grau minimo .....: {resumo['minimo']}")
    print(f"  Grau maximo .....: {resumo['maximo']}")
    print(f"  Grau medio ......: {resumo['medio']:.2f}")
    print(f"  Grau mediano ....: {resumo['mediano']:g}")
    print(f"  Vertices isolados: {resumo['isolados']}")
    print(f"  Grau impar ......: {resumo['impares']} vertice(s)")
    print(f"\n  Soma dos graus = {resumo['soma']} = 2 x {grafo.m} arestas "
          f"({'confere' if resumo['soma'] == 2 * grafo.m else 'NAO confere'}"
          " com o lema do aperto de maos)")

    print("\n  DISTRIBUICAO DOS GRAUS")
    print("  " + "-" * (LARGURA - 4))
    faixas = caracteristicas.faixas_de_grau(resumo["distribuicao"])
    maior = max(q for (_t, q) in faixas)
    for (texto, qtd) in faixas:
        print(f"  {texto:>12}: {qtd:4d}  {_barra(qtd, maior)}")

    print("\n  VERTICES DE MAIOR GRAU")
    print("  " + "-" * (LARGURA - 4))
    for (v, g) in resumo["maiores"]:
        print(f"  {g:4d}  {descreve(grafo, v)}")
    print("\n  Grau alto indica deputado presente entre os mais parecidos de")
    print("  muitos colegas: e um eixo de afinidade, ou um caso de pouca")
    print("  participacao em votacoes consensuais (ver relatorio).")


def opcao_l_euleriano(app):
    """(l) Caracteristica: grafo euleriano (teorema de Euler)."""
    cabecalho("(l) GRAFO EULERIANO")

    if not exige_grafo(app):
        return
    analise = caracteristicas.analise_euleriana(app.grafo)

    print(f"\n  Arestas conexas ..........: "
          f"{'sim' if analise['conexo'] else 'nao'} "
          f"({analise['componentes_com_aresta']} componente(s) com aresta)")
    print(f"  Vertices de grau impar ...: {len(analise['impares'])}")
    print(f"  Classificacao ............: {analise['classificacao'].upper()}")
    print(f"  Motivo ...................: {analise['motivo']}")
    print(f"\n  Para todos os graus ficarem pares seriam necessarias, no minimo,")
    print(f"  {analise['arestas_faltantes']} arestas novas (cada uma corrige dois vertices impares).")
    if analise["impares"]:
        print(f"\n  Exemplos de grau impar: {_nomes(app.grafo, analise['impares'], 4)}")


def opcao_m_hamiltoniano(app):
    """(m) Caracteristica: grafo hamiltoniano, articulacoes e pontes."""
    cabecalho("(m) GRAFO HAMILTONIANO")

    if not exige_grafo(app):
        return
    grafo = app.grafo
    analise = caracteristicas.analise_hamiltoniana(grafo)

    print("\n  Condicoes necessarias para ciclo hamiltoniano:")
    for (nome, ok) in analise["necessarias"]:
        print(f"    [{'ok' if ok else 'X '}] {nome}")
    print("\n  Condicoes suficientes:")
    for (nome, ok) in analise["suficientes"]:
        print(f"    [{'ok' if ok else 'X '}] {nome}")

    print(f"\n  Ciclo hamiltoniano ...: {analise['classificacao'].upper()}")
    print(f"  Motivo ...............: {analise['motivo']}")
    print(f"  Percurso hamiltoniano : {analise['percurso']}")
    if analise["ciclo"]:
        print(f"  Ciclo encontrado .....: {' -> '.join(map(str, analise['ciclo']))}")

    print("\n  DEPUTADOS-PONTE (VERTICES DE ARTICULACAO)")
    print("  " + "-" * (LARGURA - 4))
    if not analise["articulacoes"]:
        print("  Nenhum: retirar um unico deputado nunca desconecta o grafo.")
    for v in analise["articulacoes"]:
        print(f"  {descreve(grafo, v)}  (grau {grafo.grau(v)})")

    print("\n  ARESTAS-PONTE")
    print("  " + "-" * (LARGURA - 4))
    if not analise["pontes"]:
        print("  Nenhuma.")
    for (v, w, peso) in analise["pontes"]:
        print(f"  {descreve(grafo, v)} -- {descreve(grafo, w)}  (peso {peso})")

    if analise["grau_1"]:
        print(f"\n  Vertices de grau 1: {_nomes(grafo, analise['grau_1'], 4)}")


def opcao_n_coloracao(app):
    """(n) Caracteristica: coloracao (Welsh-Powell) e maior clique."""
    cabecalho("(n) COLORACAO DO GRAFO")

    if not exige_grafo(app):
        return
    grafo = app.grafo
    if grafo.n == 0:
        print("\n  O grafo nao possui vertices.")
        return
    analise = caracteristicas.analise_coloracao(grafo)

    print(f"\n  Cores usadas (Welsh-Powell) ..: {analise['num_cores']}")
    print(f"  Coloracao valida .............: {'sim' if analise['valida'] else 'NAO'}")
    print(f"  Maior clique (Bron-Kerbosch) .: {analise['limite_inferior']} vertice(s)")
    if analise["exato"]:
        print(f"  Numero cromatico .............: exatamente {analise['num_cores']}")
    else:
        print(f"  Numero cromatico .............: entre {analise['limite_inferior']} "
              f"e {analise['limite_superior']}")
    print(f"  Limite de Brooks (grau max+1) : {analise['limite_brooks']}")
    print(f"  Bipartido ....................: {'sim' if analise['bipartido'] else 'nao'}")

    print("\n  PARTICOES (CLASSES DE COR)")
    print("  " + "-" * (LARGURA - 4))
    for c, classe in enumerate(analise["classes"]):
        print(f"  Cor {c + 1}: {len(classe):4d} vertice(s)  ex.: {_nomes(grafo, classe, 2)}")

    print("\n  MAIOR CLIQUE (todos entre os mais parecidos uns dos outros)")
    print("  " + "-" * (LARGURA - 4))
    for v in analise["clique"]:
        print(f"  {descreve(grafo, v)}")

    print("\n  Em cada cor, nenhum par de deputados tem aresta de alta")
    print("  concordancia: cada classe e um grupo de perfis de voto distintos.")


def _amostra(linhas, recuo=""):
    """Imprime as primeiras linhas e indica quantas ficaram de fora."""
    for linha in linhas[:AMOSTRA]:
        print(f"{recuo}{linha}")
    restantes = len(linhas) - AMOSTRA
    if restantes > 0:
        print(f"{recuo}... (+{restantes} linha(s))")


def _paginar(linhas, recuo=""):
    """Imprime uma lista de linhas em blocos, aguardando o usuario."""
    for inicio in range(0, len(linhas), POR_PAGINA):
        bloco = linhas[inicio:inicio + POR_PAGINA]
        for linha in bloco:
            print(f"{recuo}{linha}")
        if inicio + POR_PAGINA < len(linhas):
            resposta = input(f"{recuo}ENTER para continuar, 'q' para parar: ")
            if resposta.strip().lower() == "q":
                break


def opcao_o_encerrar(app):
    """(o) Encerra a aplicacao, oferecendo gravar alteracoes pendentes."""
    cabecalho("(o) ENCERRAR A APLICACAO")

    if app.alterado:
        resposta = input("  Ha alteracoes nao gravadas. Gravar antes de sair? (s/n): ")
        if resposta.strip().lower() == "s":
            try:
                persistencia.gravar(app.grafo, app.caminho)
                print(f"\n  Grafo gravado em '{app.caminho}'.")
            except OSError as erro:
                print(f"\n  Nao foi possivel gravar: {erro}")
                resposta = input("  Sair mesmo assim? (s/n): ")
                if resposta.strip().lower() != "s":
                    return False

    print("\n  Encerrando a aplicacao. Ate logo!\n")
    return True


# LACO PRINCIPAL
OPCOES = {
    "a": opcao_a_ler,
    "b": opcao_b_gravar,
    "c": opcao_c_inserir_vertice,
    "d": opcao_d_inserir_aresta,
    "e": opcao_e_remover_vertice,
    "f": opcao_f_remover_aresta,
    "g": opcao_g_conteudo,
    "h": opcao_h_mostrar_grafo,
    "i": opcao_i_conexidade,
    "j": opcao_j_blocos,
    "k": opcao_k_grau,
    "l": opcao_l_euleriano,
    "m": opcao_m_hamiltoniano,
    "n": opcao_n_coloracao,
}


def executar():
    """Laco principal: mostra o menu e processa a opcao escolhida."""
    app = Aplicacao()

    while True:
        mostrar_menu(app)
        escolha = input("  Escolha uma opcao: ").strip().lower()

        if escolha == "o":
            if opcao_o_encerrar(app):
                break
            continue

        acao = OPCOES.get(escolha)
        if acao is None:
            print("\n  Opcao invalida. Escolha uma letra de [a] a [o].")
        else:
            try:
                acao(app)
            except Exception as erro:  # rede de seguranca do menu
                print(f"\n  Ocorreu um erro inesperado: {erro}")

        input("\n  Pressione ENTER para voltar ao menu...")