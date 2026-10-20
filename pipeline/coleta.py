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
    pulando os que ja estao completos. O servidor da Camara derruba a
    conexao por tempo, e nao por volume, entao o download e retomavel:
    cada tentativa continua do byte onde a anterior parou.

Historico de alteracoes:
    10/09/2026 - Isabela - Criacao do arquivo na estrutura inicial do projeto.
    14/09/2026 - Kaique - Download dos CSVs de votos e votacoes de 2024.
    14/09/2026 - Kaique - Inclusao do download do arquivo de objetos das votacoes.
    25/09/2026 - Kaique - Inclusao do download do arquivo de proposicoes afetadas.
    19/10/2026 - Isabela - Download retomavel, com verificacao de tamanho e
                           gravacao em arquivo .part, para suportar a queda de
                           conexao do servidor da Camara.
"""

import time

import requests

from utils import RAIZ

ANO_REFERENCIA = 2024

URL_VOTOS = f'https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{ANO_REFERENCIA}.csv'
URL_VOTACOES = f'https://dadosabertos.camara.leg.br/arquivos/votacoes/csv/votacoes-{ANO_REFERENCIA}.csv'
URL_OBJETOS = f'https://dadosabertos.camara.leg.br/arquivos/votacoesObjetos/csv/votacoesObjetos-{ANO_REFERENCIA}.csv'
URL_PROPOSICOES = f'https://dadosabertos.camara.leg.br/arquivos/votacoesProposicoes/csv/votacoesProposicoes-{ANO_REFERENCIA}.csv'

TEMPO_LIMITE = 120       # segundos sem resposta antes de abandonar a tentativa
TENTATIVAS = 20          # tentativas por arquivo
ESPERA = 3               # segundos entre tentativas
PARADAS_ACEITAS = 3      # tentativas seguidas sem progresso antes de desistir
PEDACO = 1024 * 1024     # bytes gravados por vez


def tamanho_no_servidor(url):
    """Tamanho do arquivo informado pelo servidor, ou None se ele nao informar."""
    try:
        resposta = requests.head(url, timeout=30, allow_redirects=True)
        if not resposta.ok:
            return None
        return int(resposta.headers['Content-Length'])
    except (requests.RequestException, KeyError, ValueError):
        return None


def tamanho_em_disco(caminho):
    return caminho.stat().st_size if caminho.exists() else 0


def continuar_download(url, parcial, inicio):
    """Grava em 'parcial' a partir do byte 'inicio', pedindo apenas o que falta.

    Grava enquanto recebe, de modo que uma queda de conexao preserve o que ja
    chegou. Se o servidor ignorar o cabecalho Range e responder com o arquivo
    inteiro (status 200 no lugar de 206), o parcial e sobrescrito em vez de
    receber o conteudo no fim, o que deixaria o arquivo invalido.
    """
    cabecalhos = {'Range': f'bytes={inicio}-'} if inicio else {}
    with requests.get(url, headers=cabecalhos, stream=True, timeout=TEMPO_LIMITE) as resposta:
        resposta.raise_for_status()
        retomou = inicio > 0 and resposta.status_code == 206
        with open(parcial, 'ab' if retomou else 'wb') as arquivo:
            for pedaco in resposta.iter_content(chunk_size=PEDACO):
                arquivo.write(pedaco)


def baixar(url, caminho):
    """Baixa o arquivo com retomada e so o considera pronto no tamanho exato.

    O download vai para um arquivo .part e e renomeado no fim. Assim um arquivo
    com o nome definitivo esta sempre completo, e nunca e um parcial que as
    etapas seguintes do pipeline leriam como se fosse o CSV inteiro.
    """
    esperado = tamanho_no_servidor(url)
    parcial = caminho.with_suffix(caminho.suffix + '.part')

    if caminho.exists():
        obtido = tamanho_em_disco(caminho)
        if esperado is None or obtido == esperado:
            print(f'{caminho.name} já existe. Pulando download.')
            return
        print(f'{caminho.name} está incompleto: {obtido} de {esperado} bytes. Retomando.')
        caminho.replace(parcial)

    print(f'Baixando {caminho.name}...')
    anterior = -1
    paradas = 0

    for tentativa in range(1, TENTATIVAS + 1):
        obtido = tamanho_em_disco(parcial)

        if esperado is not None:
            if obtido == esperado:
                parcial.replace(caminho)
                print(f'  {caminho.name}: {obtido} bytes.')
                return
            if obtido > esperado:
                print(f'  parcial maior que o esperado ({obtido} de {esperado}); recomeçando.')
                parcial.unlink()
                obtido = 0

        if obtido <= anterior:
            paradas += 1
            if paradas >= PARADAS_ACEITAS:
                raise RuntimeError(
                    f'{caminho.name}: download parado em {obtido} de {esperado} bytes. '
                    'O servidor não aceitou retomar de onde paramos.'
                )
        else:
            paradas = 0
        anterior = obtido

        try:
            continuar_download(url, parcial, obtido)
        except requests.RequestException as erro:
            print(f'  tentativa {tentativa}: {type(erro).__name__} em '
                  f'{tamanho_em_disco(parcial)} de {esperado} bytes.')
            time.sleep(ESPERA)
            continue

        if esperado is None:
            parcial.replace(caminho)
            print(f'  {caminho.name}: {tamanho_em_disco(caminho)} bytes.')
            return

    raise RuntimeError(
        f'{caminho.name}: {TENTATIVAS} tentativas sem completar '
        f'{esperado} bytes (parou em {tamanho_em_disco(parcial)}).'
    )


def baixar_dados_brutos():
    pasta = RAIZ / 'dados' / 'brutos'
    pasta.mkdir(parents=True, exist_ok=True)

    for url in [URL_VOTOS, URL_VOTACOES, URL_OBJETOS, URL_PROPOSICOES]:
        baixar(url, pasta / url.split('/')[-1])

    return pasta


if __name__ == '__main__':
    baixar_dados_brutos()
