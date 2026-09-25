# Calcular a matriz de similaridade por cosseno entre deputados
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from utils import RAIZ
from coleta import ANO_REFERENCIA

# Obstrução conta como voto contra; Abstenção e Artigo 17 (presidente) ficam neutros
VALOR_VOTO = {'Sim': 1, 'Não': -1, 'Obstrução': -1}

# Pares com menos votações em comum que isso não recebem similaridade
MINIMO_VOTACOES_EM_COMUM = 30


def matriz_de_votos(df_votos):
    """Matriz deputado x votação com +1 (a favor), -1 (contra) e 0 (neutro/ausente)."""
    df = df_votos.assign(valor=df_votos['voto'].map(VALOR_VOTO).fillna(0))
    matriz = df.pivot_table(index='deputado_id', columns='idVotacao', values='valor', fill_value=0)
    return matriz[(matriz != 0).any(axis=1)]


def similaridade_cosseno(matriz, minimo_em_comum=MINIMO_VOTACOES_EM_COMUM):
    M = matriz.to_numpy(dtype=float)
    S = cosine_similarity(M)

    votou = (M != 0).astype(float)
    em_comum = votou @ votou.T
    S[em_comum < minimo_em_comum] = np.nan

    return pd.DataFrame(S, index=matriz.index, columns=matriz.index)


if __name__ == "__main__":
    pasta_processado = RAIZ / 'dados' / 'processado'
    df_votos = pd.read_csv(pasta_processado / f'votos-{ANO_REFERENCIA}-merito.csv')

    similaridade = similaridade_cosseno(matriz_de_votos(df_votos))
    similaridade.to_csv(pasta_processado / f'similaridade-{ANO_REFERENCIA}.csv')
    print(f'Matriz {similaridade.shape[0]}x{similaridade.shape[1]} salva')
