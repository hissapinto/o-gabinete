"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/similaridade.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Terceira etapa do pipeline. Calcula a concordancia entre cada par de
    deputados: o percentual de votos coincidentes (0 a 100), considerando
    apenas as votacoes em que os dois votaram. Obstrucao conta como voto
    contra; Abstencao e Artigo 17 ficam fora da conta. Pares com menos de
    MINIMO_VOTACOES_EM_COMUM votacoes em comum ficam sem valor.

Historico de alteracoes:
    10/09/2026 - Isabela - Criacao do arquivo na estrutura inicial do projeto.
    25/09/2026 - Kaique - Calculo da matriz de similaridade por cosseno.
    26/09/2026 - Kaique - Metrica trocada para percentual de votos
                          coincidentes, calculado so nas votacoes em comum.
    14/10/2026 - Kaique - Contadores de cada par (votacoes em comum e
                          concordancias) separados, para a carga no banco.
"""

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


def contar_pares(matriz):
    """
    Contadores de cada par de deputados, só nas votações em que os dois votaram.
    Devolve duas matrizes deputado x deputado:
    - em_comum: total de votações em comum (votou @ votou.T);
    - saldo: concordâncias - discordâncias (M @ M.T, já que os votos valem +1 ou -1).
    """
    M = matriz.to_numpy(dtype=float)

    votou = (M != 0).astype(float)
    em_comum = votou @ votou.T
    saldo = M @ M.T

    return em_comum, saldo


def concordancia(matriz, minimo_em_comum=MINIMO_VOTACOES_EM_COMUM):
    """
    Percentual de votos coincidentes (0 a 100) entre cada par de deputados,
    contando só as votações em que os dois votaram (ver contar_pares).
    Pares com menos de minimo_em_comum votações em comum e a diagonal ficam NaN.
    """
    em_comum, saldo = contar_pares(matriz)

    # A conta tem que ficar exatamente assim: qualquer outra forma pode mudar a
    # última casa do float e, com ela, o arredondamento dos pesos no grafo.txt.
    with np.errstate(divide='ignore', invalid='ignore'):
        C = (saldo / em_comum + 1) / 2 * 100

    C[em_comum < minimo_em_comum] = np.nan
    np.fill_diagonal(C, np.nan)

    return pd.DataFrame(C, index=matriz.index, columns=matriz.index)


def pares_com_concordancia(matriz, minimo_em_comum=MINIMO_VOTACOES_EM_COMUM):
    """
    Uma linha por par de deputados com pelo menos minimo_em_comum votações em
    comum: o total de votações em comum e em quantas delas os dois votaram igual.
    Cada par aparece uma vez, sempre com o menor deputado_id em deputado_a.
    """
    em_comum, saldo = contar_pares(matriz)
    ids = matriz.index.to_numpy()

    linhas = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            votacoes_em_comum = int(em_comum[i, j])
            if votacoes_em_comum >= minimo_em_comum:
                # iguais + diferentes = em_comum e iguais - diferentes = saldo,
                # então iguais = (em_comum + saldo) / 2
                concordancias = (votacoes_em_comum + int(saldo[i, j])) // 2
                deputado_a = min(int(ids[i]), int(ids[j]))
                deputado_b = max(int(ids[i]), int(ids[j]))
                linhas.append((deputado_a, deputado_b, votacoes_em_comum, concordancias))

    colunas = ['deputado_a', 'deputado_b', 'votacoes_em_comum', 'concordancias']
    pares = pd.DataFrame(linhas, columns=colunas)
    return pares


if __name__ == "__main__":
    pasta_processado = RAIZ / 'dados' / 'processado'
    df_votos = pd.read_csv(pasta_processado / f'votos-{ANO_REFERENCIA}-merito.csv')

    resultado = concordancia(matriz_de_votos(df_votos))
    resultado.to_csv(pasta_processado / f'similaridade-{ANO_REFERENCIA}.csv')
    print(f'Matriz {resultado.shape[0]}x{resultado.shape[1]} salva (concordancia em %)')