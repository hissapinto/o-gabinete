# ADR-0002: Introdução do banco de dados PostgreSQL na versão web

## Contexto

O [ADR-0001](arquitetura_em_camadas.md) definiu uma arquitetura em camadas em
que o arquivo `dados/grafo.txt` é a fronteira entre o pipeline de dados e a
aplicação. Essa decisão atende a disciplina de Teoria dos Grafos, cuja
aplicação de terminal precisa ler e gravar o grafo nesse arquivo, com o formato
definido no enunciado.

A etapa TG2 de Laboratório de Engenharia de Software pede outra coisa: um
ambiente de desenvolvimento configurado e um "Hello World" que atravesse toda a
arquitetura da solução web, com frontend, backend e modelo de dados. A
arquitetura sugerida pela disciplina usa containers orquestrados por Docker
Compose, executados no GitHub Codespaces, com um banco de dados relacional
atrás de uma API.

Um arquivo texto não atende bem esse cenário. A interface web vai precisar de
consultas que o `grafo.txt` não responde de forma direta, como listar os
deputados de um partido ou montar o perfil de um deputado com seus vizinhos
mais parecidos, e o arquivo não oferece acesso concorrente nem uma interface de
consulta para a API.

## Decisão

A versão web passa a usar um banco de dados **PostgreSQL 16**, executado em
container junto com o backend e o frontend:

| Serviço | Tecnologia | Porta | Papel |
|---|---|---|---|
| `database` | PostgreSQL 16 (imagem `postgres:16-alpine`) | 5432 | Armazenamento persistente em volume Docker (`postgres_data`) |
| `backend` | FastAPI, servido por Uvicorn, acesso ao banco com `psycopg` | 8000 | API REST que consulta o banco e devolve JSON |
| `frontend` | Streamlit | 8501 | Interface web que consome a API |

Os três serviços são descritos em `docker-compose.yml`. O esquema do banco fica
em `infra/db/init/01-schema.sql`, executado automaticamente na primeira
inicialização do container. As credenciais ficam no arquivo `.env`, que não é
versionado; o repositório traz apenas o modelo `.env.example`. O ambiente de
desenvolvimento é definido em `.devcontainer/devcontainer.json` para o GitHub
Codespaces.

Nesta etapa, o modelo de dados tem uma única tabela, `app.deputado`, com dados
fictícios de teste, suficiente para provar o caminho completo: o frontend chama
a rota `/deputados` da API, que consulta o banco e devolve a lista.

O banco **não substitui** o `grafo.txt`. A aplicação de terminal de Teoria dos
Grafos continua lendo e gravando o arquivo, como definido no ADR-0001, e segue
executável sem Docker e sem dependências externas. O banco atende apenas a
versão web.

## Alternativas consideradas

**Manter apenas os arquivos (CSV e `grafo.txt`).** Não exige nenhuma
infraestrutura nova, mas obrigaria a API a ler e filtrar arquivos a cada
requisição, sem linguagem de consulta e sem controle de acesso concorrente.
Descartada para a versão web.

**SQLite.** Banco relacional em arquivo único, sem servidor, e com a mesma
linguagem SQL. Seria suficiente para o volume de dados do projeto, mas não
roda como serviço separado e se afasta da arquitetura em containers proposta
na disciplina. Fica como opção caso o ambiente em containers se mostre pesado
demais.

**PostgreSQL.** Escolhido por ser um banco relacional completo, executado como
serviço próprio, com imagem oficial para Docker e suporte maduro em Python. É a
opção alinhada à arquitetura de referência da etapa TG2.

## Consequências

- Rodar a versão web passa a exigir Docker. No Codespaces isso já vem
  configurado; localmente, basta `docker compose up`.
- O projeto passa a ter dois caminhos de dados: o `grafo.txt`, para a aplicação
  de terminal, e o banco, para a versão web. A consistência entre eles é
  responsabilidade do pipeline.
- Os dados da tabela `app.deputado` ainda são fictícios. O próximo passo é o
  pipeline carregar no banco os deputados reais e as concordâncias calculadas,
  o que exigirá novas tabelas no esquema.
- Os dados do banco sobrevivem à recriação dos containers graças ao volume
  `postgres_data`.
