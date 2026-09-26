# Calcular a matriz de concordancia entre deputados (percentual de votos coincidentes)
import numpy as np
import pandas as pd
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


def concordancia(matriz, minimo_em_comum=MINIMO_VOTACOES_EM_COMUM):
    """
    Percentual de votos coincidentes (0 a 100) entre cada par de deputados,
    contando só as votações em que os dois votaram. Como os votos valem +1 ou -1,
    M @ M.T dá (concordâncias - discordâncias) e votou @ votou.T dá o total em comum.
    Pares com menos de minimo_em_comum votações em comum e a diagonal ficam NaN.
    """
    M = matriz.to_numpy(dtype=float)

    votou = (M != 0).astype(float)
    em_comum = votou @ votou.T

    with np.errstate(divide='ignore', invalid='ignore'):
        C = ((M @ M.T) / em_comum + 1) / 2 * 100

    C[em_comum < minimo_em_comum] = np.nan
    np.fill_diagonal(C, np.nan)

    return pd.DataFrame(C, index=matriz.index, columns=matriz.index)


if __name__ == "__main__":
    pasta_processado = RAIZ / 'dados' / 'processado'
    df_votos = pd.read_csv(pasta_processado / f'votos-{ANO_REFERENCIA}-merito.csv')

    resultado = concordancia(matriz_de_votos(df_votos))
    resultado.to_csv(pasta_processado / f'similaridade-{ANO_REFERENCIA}.csv')
    print(f'Matriz {resultado.shape[0]}x{resultado.shape[1]} salva (concordancia em %)')