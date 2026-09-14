from pathlib import Path


def encontrar_raiz(marcador="requirements.txt"):
    caminho = Path.cwd()
    while not (caminho / marcador).exists():
        caminho = caminho.parent
    return caminho


RAIZ = encontrar_raiz()