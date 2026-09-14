import pandas as pd
from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar_dados_brutos


def processar_votos(pasta_brutos):
    df = pd.read_csv(
        pasta_brutos / f'votacoesVotos-{ANO_REFERENCIA}.csv',
        sep=';', encoding='utf-8-sig'
    )

    colunas_uteis = ['idVotacao', 'deputado_id', 'voto', 'deputado_siglaPartido', 'deputado_siglaUf']
    df_limpo = df[colunas_uteis]

    pasta_processado = RAIZ / 'dados' / 'processado'
    pasta_processado.mkdir(parents=True, exist_ok=True)
    df_limpo.to_csv(pasta_processado / f'votos-{ANO_REFERENCIA}-limpo.csv', index=False)

    deputados_df = df.drop_duplicates(subset='deputado_id')[
        ['deputado_id', 'deputado_nome', 'deputado_siglaPartido', 'deputado_siglaUf', 'deputado_urlFoto']
    ].copy()
    deputados_df.to_csv(pasta_processado / 'deputados.csv', index=False)


if __name__ == "__main__":
    pasta_brutos = baixar_dados_brutos()
    processar_votos(pasta_brutos)