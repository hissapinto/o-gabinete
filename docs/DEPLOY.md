# Deploy: Render + Neon (plano gratuito)

A versão web vai para a nuvem em três partes, todas gratuitas:

| Parte | Onde | Como |
|---|---|---|
| Banco PostgreSQL | **Neon** | projeto gratuito; não expira |
| API (FastAPI) | **Render**, web service | imagem do `web/api/Dockerfile` |
| Interface (HTML/JS) | **Render**, static site | arquivos de `web/frontend/`, com rewrite de `/api/*` para a API |

O Postgres gratuito do Render **não** é usado, porque expira em 30 dias. O plano gratuito do Render também não tem cron, workers nem jobs avulsos. Por isso, na nuvem, **o schema e a carga rodam uma vez, da sua máquina**, apontando para o Neon. A decisão está na [ADR-0006](adr/carga_e_deploy.md).

Os serviços do Render estão descritos no [`render.yaml`](../render.yaml) (Blueprint).

---

## 1. Criar o projeto no Neon e pegar as connection strings

1. Crie uma conta em <https://neon.com> e um projeto (**New Project**). Postgres 16 e região **AWS US East (N. Virginia)**, a mesma do Render no `render.yaml` (`region: virginia`). A API conversa com o banco a cada request, então é essa distância que importa.
2. No painel do projeto, clique em **Connect**. Há duas strings, alternadas pela chave **Connection pooling**:

| String | Como reconhecer | Use para |
|---|---|---|
| **pooled** | host com `-pooler` (ex.: `ep-xxx-pooler.us-east-1.aws.neon.tech`) | a **API** no Render |
| **direct** | host sem `-pooler` | o **schema** (`psql -f`) e a **carga** |

Por que duas: a pooled passa pelo PgBouncer do Neon em modo transação, bom para muitas conexões curtas (a API abre uma por request). A documentação do Neon recomenda a direta para migrations, `pg_dump`/`pg_restore` e operações longas ou administrativas. A carga é uma transação longa com vários `COPY`, e o schema é uma migration. Fonte: [Neon — Connection pooling](https://neon.com/docs/connect/connection-pooling).

As duas já vêm com `?sslmode=require` (e `channel_binding=require`); mantenha assim. O Neon só aceita conexão com SSL.

Guarde as duas no terminal, para os próximos passos (macOS, Linux, WSL, Git Bash):

```bash
export NEON_DIRECT='postgresql://USUARIO:SENHA@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
export NEON_POOLED='postgresql://USUARIO:SENHA@ep-xxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
```

As aspas simples são necessárias por causa do `&`. Não coloque essas strings em arquivo versionado.

## 2. Aplicar o schema

No Neon não existe o init do Docker (`/docker-entrypoint-initdb.d`), então o `01-schema.sql` é aplicado à mão, **uma vez**, pela string direta. Da raiz do repositório:

```bash
psql "$NEON_DIRECT" -v ON_ERROR_STOP=1 -f infra/db/init/01-schema.sql
```

Sem `psql` instalado, use o do container do Postgres:

```bash
docker run --rm -i postgres:16-alpine psql "$NEON_DIRECT" -v ON_ERROR_STOP=1 < infra/db/init/01-schema.sql
```

Saída esperada: um `CREATE SCHEMA`, nove `CREATE TABLE` e cinco `CREATE INDEX`. Rodar de novo dá erro `already exists`, o que é inofensivo.

## 3. Rodar a carga contra o Neon

Também uma vez só, pela string direta. Há duas formas. Ambas reaproveitam os CSVs que já estiverem em `dados/brutos/`.

**Pela imagem do compose** (não precisa de venv; precisa do Docker):

```bash
docker compose build carga
docker compose run --rm --no-deps -e DATABASE_URL="$NEON_DIRECT" carga
```

**Pelo venv** (passo 1 do README):

```bash
cd pipeline
DATABASE_URL="$NEON_DIRECT" python carga.py
cd ..
```

Leva alguns minutos na primeira vez (download de cerca de 75 MB da Câmara, se ainda não houver os CSVs, mais cerca de 20 s do layout e o envio ao Neon). O fim esperado:

```
Execucao 1: ... pares com concordancia, 2290 arestas e 535 posicoes gravados.
```

A carga é idempotente: rodar de novo imprime `2024 ja carregado (...). Pulando` e não grava nada. Para recarregar de propósito, acrescente `-e FORCAR_CARGA=1` (Docker) ou `FORCAR_CARGA=1` antes do `python`.

## 4. Criar os serviços no Render pelo Blueprint

1. Suba o repositório para o GitHub, com o `render.yaml` na raiz.
2. No Render: **New → Blueprint**, conecte o repositório e confirme. O Render lê o `render.yaml` e propõe dois serviços: `o-gabinete-api` (web service, Docker, free) e `o-gabinete` (static site).
3. Ele pede os valores marcados com `sync: false`:
   - **`DATABASE_URL`**: a string **pooled** do Neon (`$NEON_POOLED`).
   - **`CORS_ORIGINS`**: deixe **vazio**. A interface chama a API pelo rewrite `/api/*`, na mesma origem.
   Esses valores só são pedidos nessa primeira criação. Depois, troque em **o-gabinete-api → Environment**.
4. Espere os dois deploys ficarem verdes (o da API leva alguns minutos para construir a imagem).
5. **Confira o endereço da API.** O rewrite do static site aponta para `https://o-gabinete-api.onrender.com`. Se o Render tiver dado outro endereço (nome já usado por outra pessoa), corrija o `destination` no `render.yaml` e faça push, ou ajuste em **o-gabinete → Redirects/Rewrites**.

Como funciona o rewrite: o static site do Render aceita, numa regra de rewrite, um destino que seja *"a path or a full, publicly accessible URL"*, e o `*` do destino repete o trecho capturado pelo `*` da origem. Então `https://o-gabinete.onrender.com/api/anos` é servido a partir de `https://o-gabinete-api.onrender.com/anos`, sem CORS e com o mesmo `js/config.js` (`/api`) do compose. Fonte: [Render — Redirects and Rewrites](https://render.com/docs/redirects-rewrites). O destino precisa ser a URL pública: endereço interno do Render dá 502 ([fórum do Render](https://community.render.com/t/rewrite-rules-that-target-internal-urls/2940)).

**Se o rewrite não funcionar**, o plano B é chamar a API direto, com CORS:
- em `web/frontend/js/config.js`: `window.GABINETE_API_BASE = 'https://o-gabinete-api.onrender.com';`
- na API: `CORS_ORIGINS=https://o-gabinete.onrender.com`.

## 5. Checar se funcionou

```bash
# API direto (a primeira chamada pode levar ~1 min: ela estava dormindo)
curl https://o-gabinete-api.onrender.com/health
curl https://o-gabinete-api.onrender.com/anos

# a mesma rota pelo static site, passando pelo rewrite
curl https://o-gabinete.onrender.com/api/anos
```

Depois abra <https://o-gabinete.onrender.com>: o grafo de 2024 tem de aparecer; clique num deputado, use a busca e troque o tema.

No banco, entre no `psql` do Neon (string direta):

```bash
psql "$NEON_DIRECT"
# sem psql instalado:
docker run --rm -it postgres:16-alpine psql "$NEON_DIRECT"
```

E confira a execução atual e as posições dela (esperado: 535):

```sql
SELECT e.execucao_id, e.criada_em, count(p.deputado_id) AS posicoes
FROM app.execucao e
LEFT JOIN app.posicao p USING (execucao_id)
WHERE e.execucao_id = (SELECT max(execucao_id) FROM app.execucao
                       WHERE ano_inicio = 2024 AND ano_fim = 2024)
GROUP BY e.execucao_id, e.criada_em;
```

Tamanho do banco (os nossos dados ocupam cerca de 30 MB):

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));
```

---

## Limitações do plano gratuito

**Render** ([Render — Deploy for Free](https://render.com/docs/free)):

- A API **hiberna depois de 15 min** sem requests e leva **cerca de 1 min para acordar**. Enquanto isso, o Render mostra uma página de carregamento. A interface trata isso: ela tenta de novo por até ~90 s mostrando "Acordando o servidor, isso pode levar até um minuto…", e só depois mostra o erro com "Tentar novamente".
- **Dica: antes de apresentar, abra o site (ou `curl .../health`) um ou dois minutos antes.**
- 750 horas de instância gratuita por mês no workspace (a API dormindo não conta). Uma API só, sempre acordada, gasta ~720 h.
- Sem cron, workers, jobs avulsos nem shell: por isso a carga roda da sua máquina.
- O static site é gratuito, mas conta na banda de saída do mês.

**Neon** ([Neon — Plans](https://neon.com/docs/introduction/plans), [Pricing](https://neon.com/pricing)):

- **1 GB de armazenamento por projeto.** O banco carregado tem cerca de 28 MB (medido no compose: `concordancia` 13 MB, `voto` 6 MB, o resto abaixo de 1 MB). Cada recarga forçada (`FORCAR_CARGA=1`) cria uma execução nova e acrescenta ~14 MB, porque as execuções antigas ficam guardadas. Cabe com folga.
- **100 CU-hours por projeto por mês** e **suspensão após 5 min sem uso**, que não pode ser desligada. A primeira consulta depois disso demora um pouco mais enquanto o banco acorda; se passar do tempo, a API responde 503 e a interface tenta de novo.
- 5 GB de transferência por mês. A tela inicial lê o grafo uma vez (~100 KB), então isso só seria problema com dezenas de milhares de acessos.
- O plano gratuito não expira.

## Atualizar depois

- **Código da API ou da interface:** push na branch do Blueprint; o Render faz o deploy sozinho (o `buildFilter` só reconstrói o serviço cuja pasta mudou).
- **Dados:** rode a carga de novo da sua máquina (passo 3, com `FORCAR_CARGA=1`). A API lê sempre a execução mais recente; não precisa reiniciar nada.
- **Schema:** mudanças no `01-schema.sql` não chegam sozinhas ao Neon. Aplique o `ALTER`/`CREATE` correspondente com `psql "$NEON_DIRECT"`.
