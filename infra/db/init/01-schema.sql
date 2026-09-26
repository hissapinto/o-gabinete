CREATE SCHEMA app;

CREATE TABLE app.deputado (
    deputado_id   INTEGER PRIMARY KEY,
    nome          TEXT NOT NULL,
    sigla_partido TEXT,
    sigla_uf      TEXT,
    url_foto      TEXT
);

INSERT INTO app.deputado (deputado_id, nome, sigla_partido, sigla_uf, url_foto) VALUES
    (900001, 'Ana Ribeiro Fontes',      'PAB', 'SP', 'https://exemplo.invalid/fotos/900001.jpg'),
    (900002, 'Bruno Carvalho Diniz',    'PCD', 'MG', 'https://exemplo.invalid/fotos/900002.jpg'),
    (900003, 'Clara Menezes Albuquerque','PEF', 'BA', 'https://exemplo.invalid/fotos/900003.jpg'),
    (900004, 'Davi Nogueira Prado',     'PGH', 'RS', 'https://exemplo.invalid/fotos/900004.jpg'),
    (900005, 'Eliane Tavares Rocha',    'PAB', 'PE', 'https://exemplo.invalid/fotos/900005.jpg');
