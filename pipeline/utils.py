"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: pipeline/utils.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    Utilitario compartilhado do pipeline. Localiza a raiz do projeto subindo
    diretorios ate encontrar o requirements.txt, para que os caminhos de
    dados funcionem independente da pasta de onde o script e executado.

Historico de alteracoes:
    14/09/2026 - Kaique - Criacao da funcao que localiza a raiz do projeto.
    04/11/2026 - Isabela - Saida do laco quando o marcador nao existe acima
                           do diretorio atual; antes travava o import.
"""

from pathlib import Path


def encontrar_raiz(marcador="requirements.txt"):
    """
    Sobe diretorios a partir do diretorio atual ate encontrar o marcador.

    Levanta FileNotFoundError ao chegar na raiz do sistema de arquivos sem
    achar. Sem essa saida o laco nunca termina: na raiz, caminho.parent
    devolve a propria raiz. E como RAIZ e calculado no momento do import, o
    travamento aconteceria ao importar qualquer modulo do pipeline, antes de
    executar qualquer logica -- sem mensagem e sem fim.
    """
    caminho = Path.cwd()
    while not (caminho / marcador).exists():
        if caminho.parent == caminho:
            raise FileNotFoundError(
                f"{marcador} nao encontrado em {Path.cwd()} nem nos diretorios "
                "acima. Rode o pipeline de dentro do projeto."
            )
        caminho = caminho.parent
    return caminho


RAIZ = encontrar_raiz()