"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: src/negocio/filaCircular.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Fila circular disponibilizada pelo professor na disciplina de Teoria dos
    Grafos (codigo original de icalc, criado em 14/02/2023). Usada pela busca
    em largura em logica_grafos.py, no calculo das componentes conexas.

Historico de alteracoes:
    24/09/2026 - Isabela - Inclusao do codigo da aula no projeto.
"""

class FilaCircular:
    TAM_DEFAULT = 1100
    def __init__(self, tamanho=TAM_DEFAULT):
        self.fila = list(range(tamanho))
        self.inicio = 0
        self.fim = 0
        self.qtde = 0
        
       #Verifica se a fila
       #está vazia
    def isEmpty(self):
           return self.qtde == 0
  
    # Verifica se a fila está
    # cheia
    def isFull(self):
        return self.qtde == len(self.fila)
    
    # insere um elemento no final da fila
    def enqueue(self, e):
        if not self.isFull():
            self.fila[self.fim] = e
            self.fim+=1
            self.fim = self.fim % len(self.fila)
            self.qtde+=1
        else:
            print("Oveflow - Estouro de Fila")
    
    # remove um elemento do final da fila
    def dequeue(self):
        if not self.isEmpty():
            aux = self.fila[ self.inicio ]
            self.inicio+=1
            self.inicio = self.inicio % len(self.fila)
            self.qtde-=1
            return aux
        else:
            print("underflow - Esvaziamento de Fila")
            return -1
        
    # retorna quem está no início da fila
    # caso a fila não esteja vazia
    def front(self):
        if not self.isEmpty():
            return self.fila[self.inicio]
        else:
            print("underflow - Esvaziamento de Fila")
            return -1
    
    # retorna quem está no final da fila caso ela não esteja vazia
    def rear(self):
        if not self.isEmpty():
            if self.fim != 0:
                pfinal = self.fim -1
            else:
                pfinal = len(self.fila) -1
            return self.fila[pfinal]
        else:
            print("underflow - Esvaziamento de Fila")
            return -1

    # Retorna o total de elementos da fila 
    def totalElementos(self):
        return self.qtde