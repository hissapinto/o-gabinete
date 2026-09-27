"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: docs/spikes/camara_api.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Spike de consulta a API de Dados Abertos da Camara dos Deputados, usado
    para explorar os endpoints antes da definicao do pipeline.
    Documentacao: https://dadosabertos.camara.leg.br/swagger/api.html

Historico de alteracoes:
    09/09/2026 - Caio - Criacao do exemplo de integracao com a API da Camara.
"""

import requests


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


# ============================================================
# FUNÇÃO BASE PARA GET
# ============================================================

def get(endpoint, params=None):
    """Realiza uma requisição GET e retorna os dados da API."""

    response = requests.get(
        endpoint,
        params=params,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()
    return response.json()


# ============================================================
# DEPUTADOS
# ============================================================

def buscar_deputados(nome):
    """Busca deputados pelo nome."""

    data = get(
        f"{BASE_URL}/deputados",
        {
            "nome": nome,
            "ordem": "ASC",
            "ordenarPor": "nome",
            "itens": 20
        }
    )

    return data.get("dados", [])


def detalhes_deputado(deputado_id):
    """Busca informações detalhadas de um deputado."""

    data = get(f"{BASE_URL}/deputados/{deputado_id}")

    return data.get("dados", {})


def discursos_deputado(deputado_id, inicio, fim):
    """Busca discursos de um deputado em determinado período."""

    data = get(
        f"{BASE_URL}/deputados/{deputado_id}/discursos",
        {
            "dataInicio": inicio,
            "dataFim": fim,
            "ordem": "DESC",
            "ordenarPor": "dataHoraInicio",
            "itens": 20
        }
    )

    return data.get("dados", [])


# ============================================================
# VOTAÇÕES
# ============================================================

def buscar_votacoes():
    """Lista votações recentes."""

    data = get(
        f"{BASE_URL}/votacoes",
        {
            "ordem": "DESC",
            "ordenarPor": "dataHoraRegistro",
            "itens": 20
        }
    )

    return data.get("dados", [])


def detalhes_votacao(votacao_id):
    """Busca informações de uma votação."""

    data = get(f"{BASE_URL}/votacoes/{votacao_id}")

    return data.get("dados", {})


def votos_votacao(votacao_id):
    """Busca o voto de cada deputado em uma votação."""

    data = get(f"{BASE_URL}/votacoes/{votacao_id}/votos")

    return data.get("dados", [])


# ============================================================
# PARTIDOS
# ============================================================

def buscar_partidos():
    """Lista os partidos."""

    data = get(f"{BASE_URL}/partidos")

    return data.get("dados", [])


def membros_partido(partido_id):
    """Lista os membros de um partido."""

    data = get(f"{BASE_URL}/partidos/{partido_id}/membros")

    return data.get("dados", [])


# ============================================================
# EXIBIÇÃO
# ============================================================

def mostrar_deputados(deputados):

    if not deputados:
        print("\nNenhum deputado encontrado.")
        return

    print("\n" + "=" * 65)
    print(f"{'ID':<8}{'NOME':<35}{'PARTIDO/UF'}")
    print("=" * 65)

    for d in deputados:
        print(
            f"{d.get('id', '-'):<8}"
            f"{d.get('nome', '-')[:33]:<35}"
            f"{d.get('siglaPartido', '-')}/"
            f"{d.get('siglaUf', '-')}"
        )


def mostrar_votacoes(votacoes):

    if not votacoes:
        print("\nNenhuma votação encontrada.")
        return

    print("\n" + "=" * 95)
    print(f"{'ID':<25}{'DATA':<15}DESCRIÇÃO")
    print("=" * 95)

    for v in votacoes:

        id_votacao = v.get("id", "-")
        data = v.get("dataHoraRegistro", "-")
        descricao = v.get("descricao", "-")

        print(
            f"{id_votacao:<25}"
            f"{data[:10]:<15}"
            f"{descricao[:50]}"
        )

    print("=" * 95)


def mostrar_partidos(partidos):

    print("\n" + "=" * 50)
    print(f"{'ID':<8}{'SIGLA':<10}NOME")
    print("=" * 50)

    for p in partidos:
        print(
            f"{p.get('id', '-'):<8}"
            f"{p.get('sigla', '-'):<10}"
            f"{p.get('nome', '-')}"
        )


# ============================================================
# MENU
# ============================================================

def menu():

    while True:

        print("""
========================================================
             API DA CÂMARA DOS DEPUTADOS
========================================================

AVISO: Alguns endpoints ainda não estão funcionando corretamente...!

 DEPUTADOS
 [1] Buscar deputado por nome
 [2] Detalhes de deputado
 [3] Discursos de deputado

 VOTAÇÕES
 [4] Listar votações
 [5] Detalhes de votação
 [6] Votos de uma votação

 PARTIDOS
 [7] Listar partidos
 [8] Membros de um partido

 [0] Sair
========================================================
""")

        opcao = input("Escolha uma opção: ").strip()

        try:

            # ------------------------------------------------
            # DEPUTADOS
            # ------------------------------------------------

            if opcao == "1":

                nome = input("Nome do deputado: ")

                deputados = buscar_deputados(nome)

                mostrar_deputados(deputados)

            elif opcao == "2":

                id_deputado = int(
                    input("ID do deputado: ")
                )

                deputado = detalhes_deputado(id_deputado)

                print("\n" + "=" * 50)

                print(
                    f"Nome: "
                    f"{deputado.get('nome', '-')}"
                )

                print(
                    f"Nome civil: "
                    f"{deputado.get('nomeCivil', '-')}"
                )

                print(
                    f"Data de nascimento: "
                    f"{deputado.get('dataNascimento', '-')}"
                )

                print(
                    f"Escolaridade: "
                    f"{deputado.get('escolaridade', '-')}"
                )

            elif opcao == "3":

                nome = input("Nome do deputado: ")

                deputados = buscar_deputados(nome)

                if not deputados:

                    print("\n Nenhum deputado encontrado")

                if len(deputados) == 1:
                    id_deputado = deputados[0]["id"]

                inicio = input(
                    "Data inicial (AAAA-MM-DD): "
                )

                fim = input(
                    "Data final (AAAA-MM-DD): "
                )

                discursos = discursos_deputado(
                    id_deputado,
                    inicio,
                    fim
                )

                print(
                    f"\nEncontrados {len(discursos)} discursos."
                )

                for discurso in discursos:

                    print("\n" + "-" * 60)

                    print(
                        f"Data: "
                        f"{discurso.get('dataHoraInicio', '-')}"
                    )

                    print(
                        f"Tipo: "
                        f"{discurso.get('tipoDiscurso', '-')}"
                    )

                    print(
                        f"Resumo: "
                        f"{discurso.get('sumario', '-')}"
                    )

            # ------------------------------------------------
            # VOTAÇÕES
            # ------------------------------------------------

            elif opcao == "4":

                votacoes = buscar_votacoes()

                mostrar_votacoes(votacoes)

            elif opcao == "5":

                id_votacao = input(
                    "ID da votação: "
                )

                votacao = detalhes_votacao(id_votacao)

                print("\n" + "=" * 60)

                for chave, valor in votacao.items():
                    print(f"{chave}: {valor}")

            elif opcao == "6":

                  id_votacao = input(
                        "ID da votação: "
                  )

                  votos = votos_votacao(id_votacao)

                  if not votos:
                        print("\nNenhum voto individual encontrado para essa votação.")
                        print("A votação pode não ter sido nominal.")
                  else:
                        print("\n" + "=" * 65)
                        print(f"{'DEPUTADO':<40}{'VOTO'}")
                        print("=" * 65)

                        for voto in votos:

                              deputado = voto.get("deputado_", {})

                              print(
                              f"{deputado.get('nome', '-')[:38]:<40}"
                              f"{voto.get('tipoVoto', '-')}"
                              )

            # ------------------------------------------------
            # PARTIDOS
            # ------------------------------------------------

            elif opcao == "7":

                partidos = buscar_partidos()

                mostrar_partidos(partidos)

            elif opcao == "8":

                id_partido = int(
                    input("ID do partido: ")
                )

                membros = membros_partido(id_partido)

                print("\nMembros:")

                for membro in membros:
                    print(
                        f"- {membro.get('nome', '-')}"
                    )

            # ------------------------------------------------

            elif opcao == "0":

                print("\nEncerrando...")
                break

            else:

                print("\nOpção inválida.")

        except ValueError:

            print(
                "\nErro: informe um valor válido."
            )

        except requests.exceptions.RequestException as erro:

            print(
                f"\nErro ao consultar a API: {erro}"
            )

        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    menu()