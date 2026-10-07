CREATE SCHEMA app;
-- ---------------------------------------------------------------------------
-- Dados da Camara
-- ---------------------------------------------------------------------------

-- Um registro por deputado. O partido aqui e o atual, so para exibicao;
-- o partido historico fica em app.voto.
CREATE TABLE app.deputado (
    deputado_id   INTEGER PRIMARY KEY,          -- id da Camara
    nome          TEXT NOT NULL,
    sigla_partido TEXT,
    sigla_uf      TEXT,
    url_foto      TEXT
);

CREATE TABLE app.proposicao (
    proposicao_id INTEGER PRIMARY KEY,          -- id da Camara
    sigla_tipo    TEXT NOT NULL,                -- PL, PEC, MPV, PLP...
    numero        INTEGER,
    ano           SMALLINT,
    ementa        TEXT
);

-- So as votacoes que passaram no filtro de merito.
CREATE TABLE app.votacao (
    votacao_id    TEXT PRIMARY KEY,             -- id da Camara, ex.: 2355879-42
    data          DATE NOT NULL,
    ano           SMALLINT GENERATED ALWAYS AS (EXTRACT(YEAR FROM data)::SMALLINT) STORED,
    sigla_orgao   TEXT,                         -- PLEN para o Plenario
    descricao     TEXT
);

-- Uma votacao pode afetar mais de uma proposicao.
CREATE TABLE app.votacao_proposicao (
    votacao_id    TEXT    REFERENCES app.votacao (votacao_id) ON DELETE CASCADE,
    proposicao_id INTEGER REFERENCES app.proposicao (proposicao_id),
    PRIMARY KEY (votacao_id, proposicao_id)
);

-- O voto de cada deputado, com o partido que ele tinha no dia da votacao.
CREATE TABLE app.voto (
    votacao_id    TEXT    REFERENCES app.votacao (votacao_id) ON DELETE CASCADE,
    deputado_id   INTEGER REFERENCES app.deputado (deputado_id),
    voto          TEXT NOT NULL,                -- Sim, Nao, Obstrucao, Abstencao, Artigo 17
    sigla_partido TEXT,
    PRIMARY KEY (votacao_id, deputado_id)
);

-- ---------------------------------------------------------------------------
-- Resultados do pipeline
-- ---------------------------------------------------------------------------

-- Cada execucao do pipeline, com o periodo e os parametros usados.
CREATE TABLE app.execucao (
    execucao_id              SERIAL PRIMARY KEY,
    ano_inicio               SMALLINT NOT NULL,
    ano_fim                  SMALLINT NOT NULL,
    minimo_votacoes_em_comum SMALLINT NOT NULL,
    k_vizinhos               SMALLINT NOT NULL,
    concordancia_minima      SMALLINT NOT NULL,
    criada_em                TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (ano_fim >= ano_inicio)
);

-- Concordancia de todos os pares validos. Cada par aparece uma vez,
-- sempre com o menor id em deputado_a.
CREATE TABLE app.concordancia (
    execucao_id       INTEGER REFERENCES app.execucao (execucao_id) ON DELETE CASCADE,
    deputado_a        INTEGER REFERENCES app.deputado (deputado_id),
    deputado_b        INTEGER REFERENCES app.deputado (deputado_id),
    percentual        NUMERIC(5, 2) NOT NULL CHECK (percentual BETWEEN 0 AND 100),
    votacoes_em_comum INTEGER NOT NULL,
    PRIMARY KEY (execucao_id, deputado_a, deputado_b),
    CHECK (deputado_a < deputado_b)
);

-- Arestas do grafo final (os k vizinhos mais parecidos de cada deputado).
CREATE TABLE app.aresta (
    execucao_id INTEGER REFERENCES app.execucao (execucao_id) ON DELETE CASCADE,
    deputado_a  INTEGER REFERENCES app.deputado (deputado_id),
    deputado_b  INTEGER REFERENCES app.deputado (deputado_id),
    peso        SMALLINT NOT NULL CHECK (peso BETWEEN 0 AND 100),
    PRIMARY KEY (execucao_id, deputado_a, deputado_b),
    CHECK (deputado_a < deputado_b)
);

-- ---------------------------------------------------------------------------
-- Indices (as chaves primarias ja cobrem as buscas pelo primeiro campo)
-- ---------------------------------------------------------------------------

CREATE INDEX idx_votacao_ano            ON app.votacao (ano);
CREATE INDEX idx_voto_deputado          ON app.voto (deputado_id);
CREATE INDEX idx_votacao_proposicao_prop ON app.votacao_proposicao (proposicao_id);
CREATE INDEX idx_concordancia_b         ON app.concordancia (execucao_id, deputado_b);
CREATE INDEX idx_aresta_b               ON app.aresta (execucao_id, deputado_b);
