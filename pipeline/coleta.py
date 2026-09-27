"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/coleta.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Primeira etapa do pipeline. Baixa do Portal de Dados Abertos da Camara
    os arquivos CSV do ano de referencia (votos individuais, votacoes,
    objetos das votacoes e proposicoes afetadas) para dados/brutos/,
    pulando os que ja existem.

Historico de alteracoes:
    10/09/2026 - Isabela - Criacao do arquivo na estrutura inicial do projeto.
    14/09/2026 - Kaique - Download dos CSVs de votos e votacoes de 2024.
    14/09/2026 - Kaique - Inclusao do download do arquivo de objetos das votacoes.
    25/09/2026 - Kaique - Inclusao do download do arquivo de proposicoes afetadas.
"""

import requests
from utils import RAIZ

ANO_REFERENCIA = 2024

URL_VOTOS = f'https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{ANO_REFERENCIA}.csv'
URL_VOTACOES = f'https://dadosabertos.camara.leg.br/arquivos/votacoes/csv/votacoes-{ANO_REFERENCIA}.csv'
URL_OBJETOS = f'https://dadosabertos.camara.leg.br/arquivos/votacoesObjetos/csv/votacoesObjetos-{ANO_REFERENCIA}.csv'
URL_PROPOSICOES = f'https://dadosabertos.camara.leg.br/arquivos/votacoesProposicoes/csv/votacoesProposicoes-{ANO_REFERENCIA}.csv'

def baixar_dados_brutos():
    pasta = RAIZ / "dados" / "brutos"
    pasta.mkdir(parents=True, exist_ok=True)

    for url in [URL_VOTOS, URL_VOTACOES, URL_OBJETOS, URL_PROPOSICOES]:
        nome_arquivo = url.split('/')[-1]
        caminho_arquivo = pasta / nome_arquivo

        if not caminho_arquivo.exists():
            print(f'Baixando {nome_arquivo}...')
            response = requests.get(url)
            with open(caminho_arquivo, 'wb') as f:
                f.write(response.content)
        else:
            print(f'{nome_arquivo} já existe. Pulando download.')

    return pasta


if __name__ == "__main__":
    baixar_dados_brutos()