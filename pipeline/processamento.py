import pandas as pd
from utils import RAIZ
from coleta import ANO_REFERENCIA, baixar_dados_brutos

TIPOS_DE_MERITO = ['PL', 'PEC', 'MPV', 'PLP', 'PDC', 'PDL', 'PLN']

# Votações sobre o andamento da pauta, não sobre o conteúdo da proposição
PADRAO_PROCEDIMENTAL = r'requerimento|retirada de pauta|adiamento|encerramento'


def ler_csv_camara(caminho):
    return pd.read_csv(caminho, sep=';', encoding='utf-8-sig')


def processar_votos(pasta_brutos):
    df = ler_csv_camara(pasta_brutos / f'votacoesVotos-{ANO_REFERENCIA}.csv')

    colunas_uteis = ['idVotacao', 'deputado_id', 'voto', 'deputado_siglaPartido', 'deputado_siglaUf']
    df_limpo = df[colunas_uteis]

    pasta_processado = RAIZ / 'dados' / 'processado'
    pasta_processado.mkdir(parents=True, exist_ok=True)
    df_limpo.to_csv(pasta_processado / f'votos-{ANO_REFERENCIA}-limpo.csv', index=False)

    deputados_df = df.drop_duplicates(subset='deputado_id')[
        ['deputado_id', 'deputado_nome', 'deputado_siglaPartido', 'deputado_siglaUf', 'deputado_urlFoto']
    ].copy()
    deputados_df.to_csv(pasta_processado / 'deputados.csv', index=False)

    return df_limpo


def votacoes_de_merito(pasta_brutos):
    """Ids das votações de Plenário sobre o mérito de proposições legislativas."""
    df_proposicoes = ler_csv_camara(pasta_brutos / f'votacoesProposicoes-{ANO_REFERENCIA}.csv')
    df_votacoes = ler_csv_camara(pasta_brutos / f'votacoes-{ANO_REFERENCIA}.csv')

    ids_tipo = df_proposicoes.loc[
        df_proposicoes['proposicao_siglaTipo'].isin(TIPOS_DE_MERITO), 'idVotacao'
    ].unique()

    plenario = df_votacoes['siglaOrgao'] == 'PLEN'
    procedimental = df_votacoes['descricao'].fillna('').str.contains(PADRAO_PROCEDIMENTAL, case=False)

    selecionadas = df_votacoes[df_votacoes['id'].isin(ids_tipo) & plenario & ~procedimental]
    return selecionadas['id'].unique()


def filtrar_votos_merito(df_limpo, pasta_brutos):
    ids = votacoes_de_merito(pasta_brutos)
    df_merito = df_limpo[df_limpo['idVotacao'].isin(ids)]
    df_merito.to_csv(RAIZ / 'dados' / 'processado' / f'votos-{ANO_REFERENCIA}-merito.csv', index=False)
    return df_merito


if __name__ == "__main__":
    pasta_brutos = baixar_dados_brutos()
    df_limpo = processar_votos(pasta_brutos)
    df_merito = filtrar_votos_merito(df_limpo, pasta_brutos)
    print(f"{df_merito['idVotacao'].nunique()} votações de mérito, {len(df_merito)} votos")
