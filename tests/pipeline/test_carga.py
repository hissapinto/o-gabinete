"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/pipeline/test_carga.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes das funcoes que preparam os dados antes de ir para o banco. Nao
    testam a gravacao em si, que exigiria um PostgreSQL -- a suite da API ja
    cobre o banco, e esta roda sem infraestrutura.

    O foco esta no que o banco recusa: coluna NOT NULL recebendo nulo. Um
    valor invalido aqui derruba a carga inteira, porque ela roda numa
    transacao so. Foi o que aconteceu com 2026, cujo arquivo trouxe 466
    registros de voto sem valor.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao, junto do descarte de votos sem valor.
"""

import numpy as np
import pandas as pd

from carga import sem_nulos, votos_das_votacoes


def votos(linhas):
    return pd.DataFrame(
        linhas, columns=['idVotacao', 'deputado_id', 'voto', 'deputado_siglaPartido']
    )


def test_mantem_apenas_as_votacoes_pedidas():
    df = votos([
        ('v1', 100, 'Sim', 'PT'),
        ('v2', 100, 'Não', 'PT'),
        ('v3', 100, 'Sim', 'PT'),
    ])

    resultado = votos_das_votacoes(df, ['v1', 'v3'])

    assert sorted(resultado['idVotacao']) == ['v1', 'v3']


def test_descarta_voto_sem_valor():
    """
    A coluna app.voto.voto e NOT NULL. Antes deste descarte, um unico
    registro vazio derrubava a carga do ano inteiro.
    """
    df = votos([
        ('v1', 100, 'Sim', 'PT'),
        ('v1', 200, None, 'MDB'),
        ('v1', 300, 'Não', 'PL'),
    ])

    resultado = votos_das_votacoes(df, ['v1'])

    assert len(resultado) == 2
    assert 200 not in list(resultado['deputado_id'])


def test_nenhuma_coluna_de_voto_fica_nula():
    df = votos([
        ('v1', 100, 'Sim', 'PT'),
        ('v1', 200, np.nan, 'MDB'),
    ])

    resultado = votos_das_votacoes(df, ['v1'])

    assert all(v is not None for v in resultado['voto'])


def test_avisa_quando_descarta(capsys):
    """Descarte silencioso de dado e o tipo de coisa que ninguem percebe."""
    df = votos([('v1', 100, None, 'PT'), ('v1', 200, 'Sim', 'PT')])

    votos_das_votacoes(df, ['v1'])

    assert '1 votos sem valor' in capsys.readouterr().out


def test_nao_avisa_quando_nao_ha_o_que_descartar(capsys):
    df = votos([('v1', 100, 'Sim', 'PT')])

    votos_das_votacoes(df, ['v1'])

    assert capsys.readouterr().out == ''


def test_partido_nulo_e_preservado():
    """So o voto e obrigatorio; o partido do dia pode faltar sem problema."""
    df = votos([('v1', 100, 'Sim', None)])

    resultado = votos_das_votacoes(df, ['v1'])

    assert len(resultado) == 1
    assert resultado.iloc[0]['deputado_siglaPartido'] is None


def test_sem_nulos_troca_nan_por_none():
    """O psycopg grava None como NULL; NaN ele recusaria."""
    df = pd.DataFrame([(1, np.nan), (2, 'texto')], columns=['a', 'b'])

    resultado = sem_nulos(df)

    assert resultado.iloc[0]['b'] is None
    assert resultado.iloc[1]['b'] == 'texto'


def test_colunas_na_ordem_que_o_copy_espera():
    df = votos([('v1', 100, 'Sim', 'PT')])

    resultado = votos_das_votacoes(df, ['v1'])

    assert list(resultado.columns) == [
        'idVotacao', 'deputado_id', 'voto', 'deputado_siglaPartido',
    ]
