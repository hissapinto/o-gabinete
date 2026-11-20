"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_menu.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes de ponta a ponta do menu, com o dados/grafo.txt real. A entrada do
    teclado e simulada (monkeypatch de input) e a saida e capturada pelo
    pytest (capsys), de modo que cada opcao nova da parte 3 roda exatamente
    como no terminal e os resultados citados no relatorio ficam conferidos
    automaticamente.

Historico de alteracoes:
    19/11/2026 - Caio - Criacao.
    20/11/2026 - Kaique - Teste da opcao (g) com arquivo invalido.
"""

import menu


def rodar(monkeypatch, capsys, entradas):
    """Executa o menu com as entradas dadas e devolve tudo o que foi impresso."""
    fila = iter(entradas)
    monkeypatch.setattr("builtins.input", lambda _mensagem="": next(fila))
    menu.executar()
    return capsys.readouterr().out


def sessao(*opcoes):
    """Le o grafo padrao, executa as opcoes (com respostas) e encerra."""
    entradas = ["a", "", ""]           # (a) com o caminho padrao + ENTER
    for opcao in opcoes:
        entradas += opcao + [""]       # respostas da opcao + ENTER
    return entradas + ["o"]


def test_titulo_e_novas_opcoes_aparecem_no_menu(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, ["o"])

    assert "Deteccao de Blocos de Votacao" in saida
    for texto in ("[j] Detectar blocos", "[k] Grau", "[l] Grafo euleriano",
                  "[m] Grafo hamiltoniano", "[n] Coloracao", "[o] Encerrar"):
        assert texto in saida


def test_opcao_j_com_parametros_padrao(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["j", "", "", "", "n"]))

    assert "Arestas na floresta ...: 533 de 2290" in saida
    assert "BLOCOS DE VOTACAO (3)" in saida
    assert "Bloco 1: 360 deputado(s)" in saida
    assert "Bloco 2: 161 deputado(s)" in saida
    assert "Bloco 3: 14 deputado(s)" in saida
    assert "Blocos encontrados ....: Q = 0.425" in saida
    assert "Divisao por partido ...: Q = 0.392" in saida


def test_opcao_j_com_entrada_invalida_nao_quebra(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["j", "abc"], ["j", "0", "10"]))

    assert "Valor invalido" in saida
    assert "A quantidade de blocos deve estar entre 1 e 535" in saida


def test_opcao_j_mostra_sensibilidade(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["j", "", "", "", "s"]))

    assert "SENSIBILIDADE AOS PARAMETROS" in saida


def test_opcao_k_grau(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["k"]))

    assert "Grau maximo .....: 71" in saida
    assert "Grau medio ......: 8.56" in saida
    assert "4580 = 2 x 2290 arestas (confere" in saida
    assert "Roseana Sarney (MDB-MA)" in saida


def test_opcao_l_euleriano(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["l"]))

    assert "Vertices de grau impar ...: 332" in saida
    assert "NAO EULERIANO" in saida


def test_opcao_m_hamiltoniano(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["m"]))

    assert "NAO HAMILTONIANO" in saida
    assert "Rodrigo Estacho (PSD-PR)" in saida


def test_opcao_n_coloracao(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["n"]))

    assert "Cores usadas (Welsh-Powell) ..: 7" in saida
    assert "Coloracao valida .............: sim" in saida
    assert "Numero cromatico .............: entre 5 e 7" in saida


def test_opcoes_novas_exigem_grafo_carregado(monkeypatch, capsys):
    entradas = []
    for opcao in "jklmn":
        entradas += [opcao, ""]
    saida = rodar(monkeypatch, capsys, entradas + ["o"])

    assert saida.count("Nenhum grafo carregado") == 5


def test_opcao_g_com_arquivo_invalido_mostra_o_motivo(monkeypatch, capsys, tmp_path):
    """A opcao (g) passa pela mesma validacao da leitura antes de mostrar."""
    arquivo = tmp_path / "invalido.txt"
    arquivo.write_text('2\n2\n0 "Ana"\n1 "Bruno"\n1\n0 1 150\n', encoding="utf-8")
    app = menu.Aplicacao()
    app.caminho = str(arquivo)
    monkeypatch.setattr("builtins.input", lambda _m="": "n")

    menu.opcao_g_conteudo(app)
    saida = capsys.readouterr().out

    assert "Nao foi possivel mostrar o arquivo: peso fora do intervalo" in saida
    assert "Vertices ..." not in saida


def test_opcao_j_com_minimo_20_mantem_o_psol_como_bloco(monkeypatch, capsys):
    saida = rodar(monkeypatch, capsys, sessao(["j", "3", "20", "", "n"]))

    assert "Bloco 3: 14 deputado(s)" in saida
    assert "Grupo avulso" not in saida
