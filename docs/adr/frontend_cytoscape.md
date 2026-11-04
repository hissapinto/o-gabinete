# ADR-0005: Frontend em HTML/JS com Cytoscape, layout calculado no pipeline e protótipo congelado

## Status

Aceito — 04/11/2026

Autores: Caio Ariel Cardoso Saraiva, Isabela Hissa Pinto, Kaique Barros Paiva

Revisa a parte de interface da ADR-0001 (Pyvis e Streamlit) e o "Custos" da
ADR-0004 (o protótipo fora do contrato da API).

## Contexto

A ADR-0001 previa a visualização em Pyvis e Streamlit, e o `web/frontend/`
começou como um app Streamlit. Depois, para a Parte 3 de IHC, a interface foi
construída de verdade no protótipo de alta fidelidade (ADR-0004): HTML, CSS e
JavaScript puro, com o grafo desenhado pelo Cytoscape.js, lendo JSONs com o
formato das rotas da API e publicado no GitHub Pages.

A partir daí havia três problemas:

1. **Duas interfaces.** Todo o trabalho de usabilidade (busca, ficha, legenda
   com destaque, tema, celular, acessibilidade) estava no protótipo, e o
   Streamlit não tinha nada disso. Refazer tudo em Streamlit e Pyvis seria
   pior e mais caro: o Pyvis gera um HTML com vis.js dentro de um iframe, sem
   controle fino de eventos, estado na URL ou tema.
2. **O layout fora da API.** O protótipo abre o grafo com posições prontas
   (`x`/`y` em cada nó), calculadas pelo `exportar_dados.py` com o ForceAtlas2
   do NetworkX. A API não tinha esses campos. Calcular o layout no navegador
   deixaria o desenho diferente a cada abertura e lento com 535 nós.
3. **A avaliação de IHC em andamento.** O link do Pages já foi entregue e os
   testes com usuários usam aquela versão. Ela não pode mudar no meio da
   avaliação.

Ao mesmo tempo, a disciplina de Engenharia de Software exige que o front
consuma a API do grupo (FastAPI e PostgreSQL).

## Decisão

**1. O frontend da versão web passa a ser o código do protótipo.** O
`index.html`, o `css/` e o `js/` (com o Cytoscape em `js/vendor/`) foram
copiados para `web/frontend/`, que substitui o app Streamlit. O container do
frontend é um **nginx** que serve esses arquivos e repassa `/api/` para o
serviço `backend` do `docker-compose.yml`:

```nginx
location /api/ { proxy_pass http://backend:8000/; }
```

Página e API ficam na mesma origem, então não há CORS e o código não tem o
endereço da API fixo. Em `js/dados.js`, o único módulo que acessa dados, a
troca é `BASE = '/api'` sem o sufixo `.json`. O restante da interface é
idêntico ao do protótipo.

**2. O layout é calculado no pipeline e servido pela API.** O
`pipeline/layout.py` tem a mesma lógica e os mesmos parâmetros do
`exportar_dados.py`: ForceAtlas2 no modo linlog, semente 42, 1.500 iterações,
PT à esquerda, escala única nos dois eixos, nós afastados até não se
sobreporem e componentes menores encaixados no vão do desenho. A `carga.py`
calcula o layout com os vértices na ordem do `grafo.txt` e o peso inteiro das
arestas e grava o resultado em `app.posicao`:

```sql
CREATE TABLE app.posicao (
    execucao_id INTEGER REFERENCES app.execucao (execucao_id) ON DELETE CASCADE,
    deputado_id INTEGER REFERENCES app.deputado (deputado_id),
    x           DOUBLE PRECISION NOT NULL,
    y           DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (execucao_id, deputado_id)
);
```

A chave é a execução, como em `app.aresta`, para posição e arestas nunca virem
de cargas diferentes. `GET /anos/{ano}/grafo` passa a trazer `x` e `y`
(números, obrigatórios) em cada nó, com os mesmos nomes do `grafo.json` do
protótipo. Se algum nó do grafo não tiver posição, a rota responde 500 com
"Layout ausente para o ano X; rode a carga", em vez de inventar uma posição.

Validação: com o `dados/grafo.txt` como entrada, o `layout.py` reproduz as 535
posições do `web/prototipo/dados/anos/2024/grafo.json` sem nenhuma diferença.

O NetworkX entra só no `requirements.txt` do pipeline. A API não ganha
dependência nova, e o núcleo em `grafos/` continua sem biblioteca externa de
grafos (RNF03).

**3. O protótipo fica congelado em `web/prototipo/`.** Ele continua publicado
no GitHub Pages, lendo os próprios JSONs estáticos, e não recebe mais
alterações enquanto durar a avaliação de IHC. A evolução da interface
acontece em `web/frontend/`.

## Alternativas consideradas

**Manter Streamlit e Pyvis.** Não exige cópia, mas joga fora o trabalho de
IHC e entrega uma interface pior do que a que foi avaliada. Descartada.

**Um só código, com o protótipo apontando para a API.** Evitaria a
duplicação, mas o Pages não alcança a API, e qualquer mudança no front
alteraria a versão sob avaliação. Descartada enquanto durar a avaliação.

**Layout no navegador (Cytoscape `cose` ou `fcose`).** Dispensa tabela e
pipeline, mas o desenho muda a cada abertura, demora segundos com 535 nós e
não reproduz o desenho avaliado em IHC. Descartada.

**Layout calculado na API a cada pedido.** Levaria o NetworkX para a API e
custaria cerca de 20 segundos por pedido, ou um cache para cuidar. O layout só
muda quando o grafo muda, ou seja, na carga. Descartada.

**Posição chaveada por ano.** Mais simples, mas uma carga nova poderia
deixar posições e arestas de execuções diferentes. Descartada em favor da
chave por execução.

**Frontend chamando a API direto (`http://localhost:8000`) com CORS.**
Exigiria configurar CORS na API e fixar o endereço no JS, o que quebra no
Codespaces, onde cada porta tem uma URL própria. Descartada em favor do proxy
na mesma origem.

## Consequências

**Positivas**

- A versão web usa a interface avaliada em IHC, agora com dados ao vivo da
  API.
- O desenho do grafo é calculado uma vez por carga, abre na hora e é igual
  ao do protótipo.
- O contrato da API e o do protótipo voltam a coincidir: `x`/`y` deixaram de
  ser um acréscimo só do protótipo.
- O frontend não tem build nem dependência de runtime: é um nginx com
  arquivos estáticos.

**Custos**

- **Código duplicado:** `web/prototipo/` e `web/frontend/` divergem a partir
  de agora. Uma correção feita num não chega ao outro. Ao fim da avaliação de
  IHC, o grupo deve decidir se o protótipo passa a ser gerado a partir do
  `web/frontend/` ou fica arquivado.
- **Duas implementações do layout:** a do `exportar_dados.py` (congelada) e a
  do `pipeline/layout.py`. Só a segunda deve evoluir.
- **Mais uma tabela e um passo a mais na carga** (cerca de 20 segundos para
  2024). Num banco anterior a esta decisão, é preciso criar a `app.posicao`
  e rodar a carga de novo. Até lá, a rota do grafo responde 500.
- Com o volume do Postgres vazio, o `01-schema.sql` já cria a tabela; o
  passo manual vale só para bancos existentes.
