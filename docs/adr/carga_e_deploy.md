# ADR-0006: Carga como serviço de uso único no compose e deploy em Render + Neon

## Status

Aceito — 04/11/2026

Autores: Caio Ariel Cardoso Saraiva, Isabela Hissa Pinto, Kaique Barros Paiva

## Contexto

Até aqui, subir a versão web tinha um passo manual: depois do
`docker compose up`, era preciso ativar o venv, entrar em `pipeline/` e rodar
o `carga.py`. Sem isso, a interface abria sem nenhum ano disponível. Para
quem vai avaliar o projeto, é o tipo de passo que se esquece.

Ao mesmo tempo, o projeto precisa de um endereço público, de graça e sem
prazo de validade até o fim do semestre. As restrições que encontramos:

- O **Render** roda containers e sites estáticos de graça, mas não executa
  `docker compose`. O plano gratuito não tem cron, background worker, job
  avulso nem shell no container. O web service gratuito hiberna depois de
  15 minutos sem tráfego e leva cerca de 1 minuto para acordar
  ([Render — Deploy for Free](https://render.com/docs/free)).
- O **Postgres gratuito do Render expira em 30 dias**, com mais 14 de
  carência antes de apagar os dados ([mesma fonte](https://render.com/docs/free)).
- O **Neon** oferece Postgres gratuito sem expiração: 1 GB por projeto,
  100 CU-hours por mês e suspensão depois de 5 minutos sem uso
  ([Neon — Plans](https://neon.com/docs/introduction/plans)). O nosso banco
  carregado ocupa cerca de 28 MB.

E uma restrição de arquitetura (ADR-0001): o pipeline é um subsistema
offline. A carga não pode rodar dentro da API.

## Decisão

**1. Localmente, a carga é um serviço de uso único do compose.** O serviço
`carga` usa uma imagem própria (`pipeline/Dockerfile`, Python 3.12 como a
API, com o `requirements.txt` da raiz). Ele roda `pipeline/carga.py` e
termina. A ordem de subida é:

```
database (healthy) → carga (completed successfully) → backend → frontend
```

O `backend` depende da `carga` com `condition: service_completed_successfully`.
Se a carga falhar (por exemplo, com o site da Câmara fora do ar), o log
mostra `ERRO na carga de 2024: ...`, o compose não sobe a API e nada é
gravado, porque a carga roda numa transação só.

A carga é **idempotente**, e a regra mora no próprio `carga.py`, para valer
também fora do compose. Se a execução mais recente do ano já tem posições
em `app.posicao`, a carga termina sem baixar nada. A transação única garante
que uma execução gravada está completa. A exigência do layout cobre bancos
anteriores à `app.posicao`. `FORCAR_CARGA=1` recarrega mesmo assim. Os CSVs
ficam em `dados/brutos/`, montado como volume, e o `coleta.py` não baixa de
novo um arquivo que já está completo.

O Jupyter, que só o notebook de exploração usa, saiu do `requirements.txt`
e foi para o `requirements-notebook.txt`. Assim a imagem da carga não carrega
dependências de notebook.

**2. Na nuvem, Render para a API e a interface, Neon para o banco.** O
`render.yaml` (Blueprint) descreve dois serviços gratuitos:

- `o-gabinete-api`: web service com o `web/api/Dockerfile`. A API escuta em
  `0.0.0.0` na porta de `PORT`, lê `DATABASE_URL` (com `sslmode=require`,
  que o Neon exige) e só liga CORS se `CORS_ORIGINS` tiver origens.
- `o-gabinete`: static site com os arquivos de `web/frontend/` e uma regra de
  rewrite de `/api/*` para a URL pública da API. É o mesmo papel do proxy
  `/api/` do nginx no compose. O static site do Render aceita uma URL externa
  completa como destino de rewrite
  ([Render — Redirects and Rewrites](https://render.com/docs/redirects-rewrites)).
  Por isso o `js/config.js` fica com `/api` nos dois ambientes, sem build e
  sem CORS.

O banco não está no Blueprint. A API usa a connection string **pooled** do
Neon (PgBouncer em modo transação, para conexões curtas). O schema e a carga
usam a **direct**, que o Neon recomenda para migrations e operações longas
([Neon — Connection pooling](https://neon.com/docs/connect/connection-pooling)).

**3. Na nuvem, schema e carga são manuais e rodam da máquina do
desenvolvedor.** Sem cron nem jobs no plano gratuito, o `01-schema.sql` é
aplicado com `psql "$NEON_DIRECT" -f ...`, e a carga roda com
`DATABASE_URL="$NEON_DIRECT"`, pelo venv ou pela imagem `carga`. O passo a
passo está em [`docs/DEPLOY.md`](../DEPLOY.md).

A interface também passou a tolerar o servidor dormindo. Falha de rede,
tempo esgotado, 502/503/504 ou resposta que não é JSON (a página de "acordando"
do Render) são tentadas de novo, com espera crescente, por até ~90 s,
mostrando "Acordando o servidor, isso pode levar até um minuto…". Só depois
aparece o erro com "Tentar novamente".

## Alternativas consideradas

**Carga dentro da API, no startup.** Resolveria local e nuvem de uma vez,
mas viola a ADR-0001 e prende o FastAPI a pandas, NetworkX e ao download da
Câmara. Também faria cada acordar da API no Render baixar 75 MB e recalcular
o layout. Descartada.

**Carga como entrypoint do container do banco ou script de init.** O init do
Postgres não tem Python nem as dependências do pipeline, e só roda com o
volume vazio. Descartada.

**Postgres do Render.** Seria o caminho de menor atrito, tudo num Blueprint,
mas expira em 30 dias. Descartada.

**Cron job do Render para a carga.** Não existe no plano gratuito.
Descartada. A carga, de todo modo, só precisa rodar quando os dados mudam.

**Interface chamando a API pela URL completa, com CORS.** Funciona e fica
como plano B no `DEPLOY.md`. Foi preterida porque exige um `config.js`
diferente por ambiente e configurar CORS, enquanto o rewrite mantém tudo na
mesma origem.

**Imagem do nginx do `web/frontend/` como web service no Render.** Manteria o
proxy idêntico ao do compose, mas gastaria um segundo web service gratuito,
que também hiberna, para servir arquivos estáticos. Descartada.

## Consequências

**Positivas**

- `docker compose up` sobe tudo já com o grafo. Nas vezes seguintes, a carga
  pula em menos de um segundo.
- A mesma regra de idempotência vale no compose e contra o Neon.
- O deploy cabe inteiro no plano gratuito, e o banco não expira.
- A interface é a mesma nos dois ambientes (`/api`), sem build.

**Custos**

- **A primeira subida local depende do site da Câmara.** Sem os CSVs em cache
  e com a Câmara fora do ar, a API não sobe. Os CSVs ficam em `dados/brutos/`
  e as próximas subidas não dependem mais dela.
- **Passo manual na nuvem:** schema e carga são responsabilidade de quem faz
  o deploy, e mudanças futuras no schema precisam ser aplicadas à mão no Neon.
- **Primeiro acesso lento:** a API do Render hiberna depois de 15 minutos, e
  a primeira visita espera cerca de 1 minuto. O Neon suspende depois de
  5 minutos e acrescenta alguns segundos.
- **O rewrite acrescenta latência** em cada chamada à API e depende do
  endereço exato da API, que fica fixo no `render.yaml`.
- **Execuções acumulam:** cada `FORCAR_CARGA=1` grava uma execução nova
  (~14 MB no Neon). Dezenas cabem no limite de 1 GB, mas limpar execuções
  antigas é manual.
