"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: tests/grafos/test_fila_circular.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Testes da FilaCircular apresentada em aula, usada pela busca em largura de
    logica_grafos.py. O foco esta na volta dos indices: e onde uma fila
    circular erra, e o erro so aparece quando a fila enche e esvazia varias
    vezes -- exatamente o que uma busca em largura faz.

Historico de alteracoes:
    04/11/2026 - Isabela - Criacao.
"""

from filaCircular import FilaCircular


def test_fila_nova_esta_vazia():
    fila = FilaCircular(5)

    assert fila.isEmpty()
    assert not fila.isFull()
    assert fila.totalElementos() == 0


def test_respeita_a_ordem_de_chegada():
    fila = FilaCircular(5)
    for e in (10, 20, 30):
        fila.enqueue(e)

    assert [fila.dequeue() for _ in range(3)] == [10, 20, 30]
    assert fila.isEmpty()


def test_enche_na_capacidade_informada():
    fila = FilaCircular(3)
    for e in (1, 2, 3):
        fila.enqueue(e)

    assert fila.isFull()
    assert fila.totalElementos() == 3


def test_fila_cheia_nao_perde_o_que_ja_tinha():
    """O enqueue em fila cheia avisa e nao insere, em vez de sobrescrever."""
    fila = FilaCircular(2)
    fila.enqueue(1)
    fila.enqueue(2)

    fila.enqueue(99)

    assert fila.totalElementos() == 2
    assert [fila.dequeue(), fila.dequeue()] == [1, 2]


def test_fila_vazia_devolve_marca_de_erro():
    fila = FilaCircular(3)

    assert fila.dequeue() == -1
    assert fila.front() == -1
    assert fila.rear() == -1


def test_indices_dao_a_volta():
    """
    Enche, remove um e insere outro: o novo elemento ocupa a posicao 0, que
    acabou de vagar. E o caso que distingue uma fila circular de uma lista.
    """
    fila = FilaCircular(3)
    for e in (1, 2, 3):
        fila.enqueue(e)

    assert fila.dequeue() == 1
    fila.enqueue(4)

    assert fila.isFull()
    assert fila.front() == 2
    assert fila.rear() == 4
    assert [fila.dequeue() for _ in range(3)] == [2, 3, 4]


def test_sobrevive_a_varias_voltas():
    """A busca em largura enche e esvazia a fila muitas vezes seguidas."""
    fila = FilaCircular(4)
    saida = []

    for e in range(20):
        fila.enqueue(e)
        saida.append(fila.dequeue())

    assert saida == list(range(20))
    assert fila.isEmpty()


def test_front_e_rear_nao_removem():
    fila = FilaCircular(5)
    fila.enqueue(7)
    fila.enqueue(8)

    assert fila.front() == 7
    assert fila.rear() == 8
    assert fila.totalElementos() == 2
