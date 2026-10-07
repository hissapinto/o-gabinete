import os

import pandas as pd
import psycopg

from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar_dados_brutos
from processamento import ler_csv_camara


def ler_configuracao():
    """Le o .env da raiz; variaveis de ambiente ja definidas tem prioridade."""
    config = {}
    arquivo = RAIZ / '.env'
    if arquivo.exists():
        for linha in arquivo.read_text(encoding='utf-8').splitlines():
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                chave, valor = linha.split('=', 1)
                config[chave.strip()] = valor.strip()
    config.update({k: v for k, v in os.environ.items() if k.startswith('POSTGRES_')})
    return config


def conectar():
    config = ler_configuracao()
    return psycopg.connect(
        host=config.get('POSTGRES_HOST', 'localhost'),
        port=config.get('POSTGRES_PORT', '5432'),
        dbname=config['POSTGRES_DB'],
        user=config['POSTGRES_USER'],
        password=config.get('POSTGRES_PASSWORD', ''),
    )


def deputados_do_ano(pasta_brutos):
    """Um registro por deputado, com o partido do voto mais recente do ano."""
    df = ler_csv_camara(pasta_brutos / f'votacoesVotos-{ANO_REFERENCIA}.csv')
    df = df.sort_values('dataHoraVoto').drop_duplicates('deputado_id', keep='last')
    df = df[['deputado_id', 'deputado_nome', 'deputado_siglaPartido', 'deputado_siglaUf', 'deputado_urlFoto']]
    return df.astype(object).where(df.notna(), None)


def carregar_deputados(conexao, df):
    """Insere ou atualiza os deputados em lote."""
    with conexao.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO app.deputado (deputado_id, nome, sigla_partido, sigla_uf, url_foto)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (deputado_id) DO UPDATE SET
                nome          = EXCLUDED.nome,
                sigla_partido = EXCLUDED.sigla_partido,
                sigla_uf      = EXCLUDED.sigla_uf,
                url_foto      = EXCLUDED.url_foto
            """,
            [tuple(linha) for linha in df.itertuples(index=False)],
        )
    return len(df)


if __name__ == "__main__":
    pasta_brutos = baixar_dados_brutos()
    deputados = deputados_do_ano(pasta_brutos)

    with conectar() as conexao:
        total = carregar_deputados(conexao, deputados)

    print(f'{total} deputados de {ANO_REFERENCIA} gravados no banco.')