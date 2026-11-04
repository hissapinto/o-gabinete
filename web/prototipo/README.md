# O Gabinete: protótipo de alta fidelidade (IHC, Parte 3)

> **Versão congelada para IHC; o front ativo está em `web/frontend/`.**

Protótipo funcional da tela principal do O Gabinete, evoluído do esboço de baixa fidelidade (`docs/ihc/prototipo_baixa_fidelidade.jpeg`). É uma página estática feita com HTML, CSS e JavaScript puro, sem framework e sem build. O grafo é desenhado com [Cytoscape.js](https://js.cytoscape.org/) 3.30.4 (licença MIT), embutido em `js/vendor/cytoscape.min.js` (cópia do cdnjs, conferida pelo hash SRI que aparece no comentário do `index.html`). Os dados vêm de JSONs estáticos no mesmo formato da API.

## Como rodar localmente

A pasta `web/prototipo/` é autossuficiente: nenhum arquivo dela aponta para fora da pasta e o Cytoscape vai junto, então o grafo carrega mesmo sem acesso a CDN. A internet só é usada para as fontes (Google Fonts; sem elas, entram as fontes do sistema) e para as fotos dos deputados (site da Câmara; sem elas, aparece o avatar com iniciais).

A página precisa ser servida por HTTP, porque o navegador não deixa um arquivo aberto direto do disco (`file://`) ler os JSONs. Quem clicar duas vezes no `index.html` vê um aviso explicando isso, com o comando abaixo pronto para copiar:

```bash
cd web/prototipo          # ou a pasta extraída do prototipo.zip
python -m http.server 8000
# abra http://localhost:8000
```

O `web/prototipo.zip` traz a mesma pasta pronta para enviar, sem venvs nem caches.

## Como publicar no GitHub Pages (para quem é dono do repositório)

O protótipo não tem build: o GitHub Pages serve os arquivos como estão. É preciso ser dono (ou admin) do repositório. Em conta gratuita, o repositório precisa ser **público**.

1. **Envie os arquivos.** Confira que `web/prototipo/` está commitado e no GitHub, **incluindo `web/prototipo/dados/`**, porque sem os JSONs a página abre no cartão de erro. Use a branch que vai ser publicada (normalmente `main`).
2. **Ative o Pages.** No repositório, abra **Settings → Pages**. Em *Build and deployment → Source*, escolha **Deploy from a branch**. Em *Branch*, selecione `main` e a pasta **`/ (root)`** e clique em **Save**.
3. **Espere a publicação.** A aba **Actions** mostra o job *pages build and deployment*. Quando ele ficar verde (1 a 3 minutos), o topo de **Settings → Pages** mostra o endereço do site.
4. **Monte o link do protótipo:** `https://<dono>.github.io/<repositorio>/web/prototipo/`. O endereço diferencia maiúsculas de minúsculas; a barra final é recomendada.
5. **Teste numa janela anônima** e no celular, e coloque o link no `ENTREGA.txt`.

Depois disso, cada push na branch publicada atualiza o site sozinho.

**Se der problema:**
- **404:** a publicação ainda não terminou (veja a aba Actions) ou o caminho está errado (confira `web/prototipo/` e as maiúsculas).
- **Página abre, mas mostra "Não foi possível carregar os dados":** a pasta `dados/` não foi enviada.
- **Job do Pages falha no Jekyll:** crie um arquivo vazio `.nojekyll` na raiz do repositório e faça push. Isso desliga o processamento Jekyll, que este site não usa. Hoje o repositório não tem nada que quebre o Jekyll; é só uma garantia.

## Melhorias de IHC em relação ao esboço

1. **Sem a tela placeholder "grafo vazio, escolha o ano":** a página abre direto no ano mais recente. O esboço exigia uma escolha antes de mostrar qualquer coisa.
2. **Três formas de sair do modo deputado:** clique no fundo do grafo, tecla **Esc** ou o botão **"Voltar ao grafo completo"**, que aparece no painel e sobre o grafo. O botão Voltar do navegador também funciona.
3. **Busca com autocomplete:** aceita nome, partido ou UF, ignora acentos e maiúsculas (`joao` encontra "João") e destaca o trecho que bateu. Só sugere quem está no grafo, então não existe busca que dá em nada. Funciona pelo teclado: `/` foca a busca, setas navegam, Enter abre e Esc fecha.
4. **Tooltip ao passar o mouse** sobre um nó, com nome, partido e UF. No modo deputado, o tooltip também mostra a posição do deputado entre os mais similares e o percentual.
5. **Estados de carregamento e erro visíveis:** spinner ao carregar o grafo, esqueleto da lista ao abrir a ficha e cartão de erro com ação ("Tentar novamente" ou "Abrir 2024") quando um JSON não é encontrado, quando um ano não tem grafo ou quando a biblioteca do grafo não carrega. Deputado inexistente na URL gera um aviso discreto.
6. **Legenda clicável, com prévia:** todos os 20 partidos aparecem com cor própria. Passar o mouse (ou o foco do teclado) num partido mostra uma prévia do destaque, e clicar fixa o destaque: os deputados do partido ficam na frente, com contorno, e o resto é esmaecido. Um aviso sobre o grafo ("PSOL destacado · 13 deputados ×") lembra o que está filtrado. Desfaz com novo clique, com o × do aviso, clicando no fundo ou com Esc. A legenda é o desambiguador principal das cores parecidas.
7. **Seletor de ano sempre visível:** os anos da legislatura que ainda não têm dados aparecem desabilitados, com "em breve", em vez de sumirem.
8. **Números ligam a lista ao grafo:** como as letras A–E do esboço, os 5 mais similares recebem no grafo um selo com o mesmo número (1–5) da lista do painel, na fonte da interface. Passar o mouse num item da lista realça o nó correspondente, e clicar no item abre aquele deputado. O nome do selecionado vai para o lado (acima, abaixo, direita ou esquerda) que não cobre nenhum selo, e o zoom tem limite (1,3×), para o contexto ao redor não virar bolhas gigantes.
9. **Link compartilhável:** o estado fica na URL (`#2024/220593`), então dá para mandar o link de um deputado específico para quem vai testar.
10. **Painel "Como ler o grafo"**, que explica ponto, cor e espessura da linha. Ele substitui a legenda abstrata "espessura = similaridade" do wireframe.
11. **Celular:** o painel lateral vira uma gaveta na base da tela. No modo deputado ela abre sozinha e o grafo encolhe para o destaque não ficar escondido. Há botões de zoom (aproximar, afastar e **Enquadrar grafo**, que mostra o desenho inteiro), cada um com dica e `aria-label`, para quem não usa roda do mouse ou pinça.
12. **Tema claro ou escuro:** botão sol/lua no topo, com dica e `aria-label`. Sem escolha, segue o sistema (`prefers-color-scheme`), inclusive se ele mudar com a página aberta. A escolha fica salva no navegador (`localStorage`, com fallback se ele estiver bloqueado), é aplicada antes do CSS (sem piscar o tema errado) e repinta o grafo na hora, sem recarregar.
13. **Acessibilidade:** a busca segue o padrão *combobox* da WAI-ARIA, há foco visível em todos os controles e link "pular para o painel", e o movimento é reduzido quando o sistema pede (`prefers-reduced-motion`).

### Decisões visuais

- **Cores dos partidos:** cada um dos 20 partidos tem cor própria. A paleta foi escolhida por otimização e medida par a par em distância OKLab ×100, com simulação de deuteranopia de Machado et al. (2009). As 10 maiores bancadas foram priorizadas; as menores podem ser mais parecidas entre si, mas ficam longe de todas as maiores:

  | Grupo | Visão normal (piso 15) | Deuteranopia (alvo 8) |
  |---|---|---|
  | Entre os 10 maiores | **18,0** (PT × UNIÃO) | **9,7** (PT × PP) |
  | Menores × maiores | 12,5 (PSDB × PSD) | 7,4 (SOLIDARIEDADE × UNIÃO) |
  | Entre os 10 menores | 10,1 (AVANTE × NOVO) | 5,9 (PRD × PV) |
  | Geral (os 20) | 10,1 | 5,9 |

  Com 20 cores não dá para todo par passar dos pisos, por isso a identificação não depende só da cor: há tooltip com o partido, legenda com prévia e destaque, e o nome do partido na ficha e na lista. Partido novo, sem cor definida, cai num cinza de reserva (`--partido-outro`).
- **Temas:** toda cor é um token CSS no `:root` de `css/estilo.css`, inclusive as do grafo (`--grafo-*`) e as dos partidos (`--partido-*`), que o JavaScript lê de lá. Há duas variantes: **clara neutra** (sem cor de marca, para não competir com os partidos) e **escura** (grafo sobre fundo escuro, nós com contorno claro fino), trocadas pelo botão do topo.
- **Espessura da aresta:** é normalizada pelo intervalo real dos pesos do ano (mínimo a máximo), e não pela escala de 0 a 100, porque os pesos se concentram entre 94% e 100%.
- **Layout:** é pré-calculado em Python, com o ForceAtlas2 do NetworkX (modo *linlog*, 1.500 iterações, semente fixa), por isso o grafo abre instantâneo e sempre com o mesmo desenho. O *linlog* separa os três blocos (esquerda, centro e direita) sem achatá-los numa faixa: a proporção fica em ~2:1, contra ~3,5:1 no modo padrão. A escala é a mesma nos dois eixos. Cada componente conexo é deitado no seu eixo de maior espalhamento, com o PT fixado à esquerda só para o desenho não espelhar entre execuções, e os nós são afastados até não se sobreporem. Componentes menores (em 2024, o PSOL forma um à parte) são encaixados no vão livre mais próximo do desenho principal, sem abrir espaço vazio.
- **Nitidez:** o Cytoscape usa `pixelRatio: 'auto'` (resolução real da tela), `textureOnViewport: false` e `motionBlur: false`, e um `ResizeObserver` chama `cy.resize()` sempre que a área do grafo muda de tamanho.

## Estrutura

```
web/prototipo/
  index.html            página única
  css/estilo.css        tokens (cor, tipo, espaço) e layout desktop/celular
  js/dados.js           ÚNICO acesso a dados (carregarAnos, carregarGrafo, carregarDeputado)
  js/app.js             estado, URL, carregamento e erro
  js/grafo.js           Cytoscape: desenho, foco, destaque de partido
  js/painel.js          legenda, estatísticas e ficha do deputado
  js/busca.js           autocomplete
  js/partidos.js        cores dos partidos (lidas do CSS)
  js/tema.js            botão de tema claro/escuro
  js/dom.js             utilitários de DOM e formatação
  js/vendor/            Cytoscape.js 3.30.4 embutido (cytoscape.min.js)
  dados/                JSONs gerados pelo exportar_dados.py
  exportar_dados.py     gera os JSONs (API local ou dados/grafo.txt)
  requirements.txt      networkx e numpy, só para o exportador
  ENTREGA.txt           link do protótipo e integrantes
  relatorio_casamento.txt  deputados sem id da Câmara (gerado)
```

## Contrato dos JSONs

Os arquivos espelham as rotas da API (`web/api/rotas/`). Para trocar pela API real, em `js/dados.js` basta mudar `BASE` para a URL da API e deixar `SUFIXO` vazio.

| Arquivo | Rota da API |
|---|---|
| `dados/anos.json` | `GET /anos` |
| `dados/anos/<ano>/grafo.json` | `GET /anos/{ano}/grafo` |
| `dados/anos/<ano>/deputados/<id>.json` | `GET /anos/{ano}/deputados/{id}` |

```jsonc
// GET /anos — do mais recente ao mais antigo
{ "anos": [{ "ano": 2024 }] }

// GET /anos/2024/grafo — nós em ordem de nome; aresta com o menor id em deputado_a
{
  "ano": 2024,
  "nos": [
    { "deputado_id": 220593, "nome": "Abilio Brunini", "sigla_partido": "PL",
      "sigla_uf": "MT", "x": 925.2, "y": 11.1 }       // x, y: NOVOS, fora do contrato da API
  ],
  "arestas": [
    { "deputado_a": 73579, "deputado_b": 220593, "percentual": 95.0 }
  ]
}

// GET /anos/2024/deputados/220593
{
  "ano": 2024,
  "deputado": { "deputado_id": 220593, "nome": "Abilio Brunini", "sigla_partido": "PL",
                "sigla_uf": "MT", "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/220593.jpg" },
  "mais_similares": [
    { "deputado_id": 227991, "nome": "Dr Flávio", "sigla_partido": "PL",
      "percentual": 100.0, "votacoes_em_comum": null }
  ]
}
```

- **`x` e `y`** são o único acréscimo ao contrato: a posição pré-calculada do nó, em pixels do Cytoscape. A API ainda não devolve esses campos.
- **`percentual`** é número. No banco ele é `NUMERIC(5,2)`, que o FastAPI serializa como float.
- **`url_foto`** pode ser `null`. Nesse caso a ficha mostra um avatar com as iniciais.

## Gerar os dados

```bash
cd web/prototipo
pip install -r requirements.txt
python exportar_dados.py                    # limiar 75%, sem corte extra (igual ao pipeline)
python exportar_dados.py --limiar 90 --k 3  # grafo mais enxuto (UC01, extensão 3a)
python exportar_dados.py --sem-camara       # fallback sem consultar a Câmara
```

O script tenta primeiro a **API local** (`docker compose up`, em `http://localhost:8000`) e salva as respostas como vieram, acrescentando só o layout. Se a API não responder, ele gera a partir de **`dados/grafo.txt`**, imitando os endpoints. Nesse fallback:

- O `grafo.txt` só tem o índice do vértice. O id e a foto vêm da API de Dados Abertos da Câmara (legislatura 57, uma leitura só), casando por nome e UF. Quem não casa recebe o id sintético `9000000 + índice` e fica sem foto, e a lista dessas pessoas vai para `relatorio_casamento.txt`. Na exportação atual, 534 de 535 casaram. A exceção é Michele Collins (PP-PE).
- O `percentual` sai inteiro (95.0 em vez de 95.37), porque o `grafo.txt` arredonda.
- `votacoes_em_comum` sai como `null`, porque o `grafo.txt` não guarda esse número.
- `mais_similares` traz os 5 vizinhos de maior peso no `grafo.txt`, ordenados por percentual. A API usa a concordância completa, inclusive pares abaixo do corte.
- Só o ano de **2024** é exportado, porque o `grafo.txt` cobre um ano só.

`--limiar` e `--k` cortam apenas as arestas desenhadas. Os nós continuam todos, como faz a API, e a lista de mais similares não muda.
