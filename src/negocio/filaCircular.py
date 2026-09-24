"""
Created on Tue Feb 14 19:40:58 2023

@author: icalc
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
        

