# ADR-0004: Protótipo de alta fidelidade publicado como site estático

## Status

Aceito — 29/10/2026

Autores: Caio Ariel Cardoso Saraiva, Isabela Hissa Pinto, Kaique Barros Paiva

## Contexto

A disciplina de Interação Humano-Computador pede, na Parte 3, um protótipo de
alta fidelidade — não um desenho, mas algo navegável, que o avaliador possa
abrir e usar.

A versão web do projeto não serve a esse propósito. Para vê-la funcionando é
preciso ter Docker instalado, subir três containers, criar o `.env`, baixar
cerca de 73 MB de CSVs da Câmara e rodar o `carga.py`. É muito a pedir de quem
só quer avaliar a interface, e qualquer tropeço nessa sequência vira uma
avaliação prejudicada por motivo alheio ao que está sendo avaliado.

O GitHub Pages resolveria o acesso — basta um link —, mas serve apenas arquivos
estáticos: não executa a API em FastAPI, nem o frontend em Streamlit, nem o
PostgreSQL.

## Decisão

Um protótipo em HTML, CSS e JavaScript puro, em `web/prototipo/`, publicado pelo
GitHub Pages a partir da `main`, e que lê **arquivos JSON cujos caminhos imitam
as rotas da API**:

| Arquivo estático | Rota equivalente |
|---|---|
| `dados/anos.json` | `GET /anos` |
| `dados/anos/<ano>/grafo.json` | `GET /anos/{ano}/grafo` |
| `dados/anos/<ano>/deputados/<id>.json` | `GET /anos/{ano}/deputados/{id}` |

O único acréscimo ao contrato é que cada nó do grafo carrega as coordenadas `x`
e `y`, calculadas na exportação com o NetworkX, para o navegador abrir o grafo
já desenhado e sempre com o mesmo layout.

A consequência dessa escolha é que **o mesmo código de interface serve aos dois
mundos**. Trocar a fonte são duas constantes em `web/prototipo/js/dados.js`:

```js
const BASE = 'dados';   // API real: 'http://localhost:8000'
const SUFIXO = '.json'; // API real: ''
```

O `exportar_dados.py` gera esses arquivos, preferindo a API local quando ela
responde — assim as respostas são salvas como vieram, o que garante o contrato —
e recorrendo ao `dados/grafo.txt` quando não. O Cytoscape.js, usado para
desenhar o grafo, é versionado em `js/vendor/` em vez de vir de CDN.

## Alternativas consideradas

**Hospedar a aplicação inteira.** Resolveria sem duplicar nada, e o protótipo
mostraria dados sempre atuais. Descartada pelo custo e pela operação: exigiria
um serviço com banco gerenciado, credenciais e um responsável por mantê-lo no ar
até a avaliação, para um projeto de disciplina com prazo fechado.

**Imagens estáticas das telas.** O caminho mais barato. Descartada porque não é
protótipo de alta fidelidade: não se navega, não se busca um deputado, não se
clica numa aresta — justamente o que a Parte 3 avalia.

**Reescrever o protótipo com dados embutidos no próprio HTML.** Simples e sem
pasta de JSONs. Descartada porque romperia a correspondência com o contrato da
API, e o protótipo deixaria de poder ser apontado para o backend real.

## Consequências

**Positivas**

- O protótipo é acessível por um link, sem instalar nada:
  <https://hissapinto.github.io/o-gabinete/web/prototipo/>
- A interface do protótipo e a da versão conectada são o mesmo código; apontar
  para a API real custa duas linhas.
- Publicação automática: cada push na `main` republica o site.
- O formato dos JSONs funciona como verificação viva do contrato da API — se as
  rotas mudarem de formato, a próxima exportação acusa.

**Custos**

- Os JSONs são um retrato de uma carga, e não se atualizam quando o `carga.py`
  roda de novo; regerá-los é um passo manual, com o `exportar_dados.py`.
- O protótipo e a API precisam ser mantidos em acordo: uma mudança no formato de
  resposta exige nova exportação, senão os dois divergem silenciosamente.
- Quando a exportação recorre ao `grafo.txt`, o casamento de deputados é feito
  por nome e UF contra a API de Dados Abertos; quem não casar recebe id
  sintético e fica sem foto, e é registrado em `relatorio_casamento.txt`.
- O repositório passa a versionar centenas de arquivos JSON gerados.
