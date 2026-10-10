"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/apresentacao/menu.py

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
"""

import persistencia
from grafo import GrafoPonderadoND
import logica_grafos

LARGURA = 66
POR_PAGINA = 20  # vertices por pagina na opcao (h)
AMOSTRA = 10     # linhas exibidas no resumo da opcao (g)


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
  [j] Encerrar a aplicacao
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


def opcao_j_encerrar(app):
    """(j) Encerra a aplicacao, oferecendo gravar alteracoes pendentes."""
    cabecalho("(j) ENCERRAR A APLICACAO")

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
}


def executar():
    """Laco principal: mostra o menu e processa a opcao escolhida."""
    app = Aplicacao()

    while True:
        mostrar_menu(app)
        escolha = input("  Escolha uma opcao: ").strip().lower()

        if escolha == "j":
            if opcao_j_encerrar(app):
                break
            continue

        acao = OPCOES.get(escolha)
        if acao is None:
            print("\n  Opcao invalida. Escolha uma letra de [a] a [j].")
        else:
            try:
                acao(app)
            except Exception as erro:  # rede de seguranca do menu
                print(f"\n  Ocorreu um erro inesperado: {erro}")

        input("\n  Pressione ENTER para voltar ao menu...")