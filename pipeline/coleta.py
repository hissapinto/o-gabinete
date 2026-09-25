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