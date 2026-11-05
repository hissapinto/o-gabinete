"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_persistencia.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da leitura e da gravacao do grafo.txt, cujo formato e definido pelo
    enunciado da disciplina. O teste central e o de ida e volta: gravar um
    grafo e ler de volta tem de devolver o mesmo grafo, porque e assim que o
    pipeline e a aplicacao de terminal se comunicam.

    Todos os arquivos sao escritos em pasta temporaria do pytest, de modo que
    o dados/grafo.txt do repositorio nunca e tocado.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

import pytest

import persistencia
from grafo import GrafoPonderadoND


@pytest.fixture
def grafo():
    g = GrafoPonderadoND(3)
    g.rotulos = ["Ana Ribeiro (PT-SP)", "Bruno Castro (PL-RJ)", "Carla Dias (MDB-MG)"]
    g.insereA(0, 1, 90)
    g.insereA(1, 2, 75)
    return g


def escrever(tmp_path, texto):
    caminho = tmp_path / "grafo.txt"
    caminho.write_text(texto, encoding="utf-8")
    return str(caminho)


# --- ida e volta -----------------------------------------------------------

def test_gravar_e_ler_devolve_o_mesmo_grafo(tmp_path, grafo):
    caminho = str(tmp_path / "saida.txt")

    assert persistencia.gravar(grafo, caminho) == 2

    lido = persistencia.ler(caminho)
    assert lido.n == grafo.n
    assert lido.m == grafo.m
    assert lido.rotulos == grafo.rotulos
    assert lido.arestas() == grafo.arestas()


def test_rotulo_com_acento_sobrevive_a_ida_e_volta(tmp_path):
    g = GrafoPonderadoND(2)
    g.rotulos = ["Átila Município (PSB-CE)", "João D'Ávila (PP-BA)"]
    g.insereA(0, 1, 42)
    caminho = str(tmp_path / "acentos.txt")

    persistencia.gravar(g, caminho)

    assert persistencia.ler(caminho).rotulos == g.rotulos


def test_grafo_sem_arestas_sobrevive_a_ida_e_volta(tmp_path):
    g = GrafoPonderadoND(2)
    g.rotulos = ["A", "B"]
    caminho = str(tmp_path / "vazio.txt")

    assert persistencia.gravar(g, caminho) == 0
    lido = persistencia.ler(caminho)

    assert lido.n == 2
    assert lido.m == 0


def test_gravacao_cria_a_pasta_que_faltar(tmp_path, grafo):
    caminho = str(tmp_path / "nova" / "pasta" / "grafo.txt")

    persistencia.gravar(grafo, caminho)

    assert persistencia.ler(caminho).n == 3


# --- formato ---------------------------------------------------------------

def test_le_rotulo_sem_aspas(tmp_path):
    caminho = escrever(tmp_path, "2\n2\n0 Ana\n1 Bruno\n1\n0 1 50\n")

    lido = persistencia.ler(caminho)

    assert lido.rotulos == ["Ana", "Bruno"]
    assert lido.peso(0, 1) == 50


def test_le_rotulo_entre_aspas_com_espacos(tmp_path):
    caminho = escrever(tmp_path, '2\n2\n0 "Ana Ribeiro (PT-SP)"\n1 "Bruno"\n0\n')

    assert persistencia.ler(caminho).rotulos[0] == "Ana Ribeiro (PT-SP)"


def test_ignora_linhas_em_branco(tmp_path):
    caminho = escrever(tmp_path, '2\n\n2\n0 "Ana"\n\n1 "Bruno"\n1\n0 1 50\n\n')

    assert persistencia.ler(caminho).m == 1


def test_conteudo_devolve_o_arquivo_bruto(tmp_path):
    texto = '2\n1\n0 "Ana"\n0\n'
    caminho = escrever(tmp_path, texto)

    assert persistencia.conteudo(caminho) == texto


# --- erros -----------------------------------------------------------------

def test_arquivo_inexistente(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="nao encontrado"):
        persistencia.ler(str(tmp_path / "nao_existe.txt"))


def test_conteudo_de_arquivo_inexistente(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo):
        persistencia.conteudo(str(tmp_path / "nao_existe.txt"))


def test_arquivo_vazio(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="vazio ou incompleto"):
        persistencia.ler(escrever(tmp_path, "2\n"))


def test_tipo_de_grafo_diferente_do_esperado(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="nao suportado"):
        persistencia.ler(escrever(tmp_path, '1\n1\n0 "Ana"\n0\n'))


def test_tipo_nao_numerico(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="tipo do grafo"):
        persistencia.ler(escrever(tmp_path, 'dois\n1\n0 "Ana"\n0\n'))


def test_faltam_linhas_de_vertice(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="faltam linhas de vertice"):
        persistencia.ler(escrever(tmp_path, '2\n3\n0 "Ana"\n1 "Bruno"\n'))


def test_indice_de_vertice_fora_da_faixa(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="indice de vertice invalido"):
        persistencia.ler(escrever(tmp_path, '2\n2\n0 "Ana"\n9 "Bruno"\n0\n'))


def test_aresta_mal_formada(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="mal formada"):
        persistencia.ler(escrever(tmp_path, '2\n2\n0 "Ana"\n1 "Bruno"\n1\n0 1\n'))


def test_faltam_linhas_de_aresta(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="faltam linhas de aresta"):
        persistencia.ler(escrever(tmp_path, '2\n2\n0 "Ana"\n1 "Bruno"\n2\n0 1 50\n'))


def test_aresta_com_vertice_inexistente(tmp_path):
    with pytest.raises(persistencia.ErroDeArquivo, match="aresta invalida"):
        persistencia.ler(escrever(tmp_path, '2\n2\n0 "Ana"\n1 "Bruno"\n1\n0 9 50\n'))
