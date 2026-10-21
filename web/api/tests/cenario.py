"""
O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
Arquivo: web/api/tests/cenario.py

Integrantes:
    Caio Ariel Cardoso Saraiva  - RA 10439611
    Isabela Hissa Pinto         - RA 10441873
    Kaique Barros Paiva         - RA 10441787

Sintese:
    O cenario de teste em um unico lugar: os dados gravados no banco e os
    numeros que deles decorrem. Os testes importam as constantes daqui em vez
    de repetir valores, para que mudar o cenario nao exija cacar numeros
    espalhados pelos arquivos.

    Os votos cobrem as armadilhas da RN01 (Obstrucao conta como voto contra;
    Abstencao e Artigo 17 ficam fora; votacao de outro ano nao entra) e os
    desfechos de cada endpoint: deputado no grafo, deputado que votou mas
    ficou fora, quem nunca votou, ano com e sem execucao, e duas execucoes no
    mesmo ano para provar que vale a mais recente.

    Sobre os tres empatados em 60.00: com apenas dois, a ordem alfabetica
    coincidiria com a ordem por id crescente ou com a decrescente, e o teste
    do desempate passaria mesmo se o criterio fosse o id. Com tres, os ids
    600, 150 e 200 com os nomes Alberto, Beatriz e Bruno dao a ordem
    [600, 150, 200], que nao e nem a crescente nem a decrescente por id.

Historico de alteracoes:
    21/10/2026 - Isabela - Criacao, junto da suite de testes do web/api.
"""

# --- deputados -------------------------------------------------------------
ANA = 100       # no grafo, aparece como deputado_a em todos os seus pares
BEATRIZ = 150   # no grafo, empatada em percentual com Bruno e Alberto
BRUNO = 200     # no grafo, e deputado_b num par e deputado_a em outro
CARLA = 300     # no grafo, com o maior percentual junto de Ana
DIEGO = 400     # votou em 2024, mas ficou fora do grafo
ELENA = 500     # cadastrado e nunca votou
ALBERTO = 600   # no grafo, empatado em percentual com Beatriz e Bruno

NOMES = {
    ANA: "Ana Ribeiro",
    BEATRIZ: "Beatriz Lima",
    BRUNO: "Bruno Castro",
    CARLA: "Carla Dias",
    DIEGO: "Diego Alves",
    ELENA: "Elena Moraes",
    ALBERTO: "Alberto Nunes",
}

# --- anos ------------------------------------------------------------------
ANO = 2024             # ano com grafo
ANO_ANTERIOR = 2023    # tem execucao, mas nenhuma concordancia calculada
ANO_SEM_EXECUCAO = 2019

# --- execucoes -------------------------------------------------------------
EXECUCAO_ANTIGA = 1    # 2024, dados propositalmente errados
EXECUCAO_ATUAL = 2     # 2024, a que vale (maior execucao_id)
EXECUCAO_2023 = 3

# --- numeros que decorrem dos votos abaixo ---------------------------------
# par (menor_id, maior_id): (votacoes_em_comum, concordancias, percentual)
PARES = {
    (ANA, BEATRIZ): (5, 3, "60.00"),
    (ANA, BRUNO):   (5, 3, "60.00"),
    (ANA, CARLA):   (3, 3, "100.00"),
    (ANA, ALBERTO): (5, 3, "60.00"),
    (BRUNO, CARLA): (3, 2, "66.67"),
}

# Votacoes de 2024 em que Ana e Bruno concordaram e divergiram, da mais
# recente para a mais antiga, que e a ordem que a consulta devolve.
ANA_BRUNO_CONCORDARAM = ["v3", "v2", "v1"]
ANA_BRUNO_DIVERGIRAM = ["v5", "v4"]

# Mais similares a Ana: Carla na frente por percentual, e os tres empatados
# em 60.00 em ordem alfabetica de nome.
SIMILARES_DE_ANA = [CARLA, ALBERTO, BEATRIZ, BRUNO]
EMPATADOS_COM_ANA = ["Alberto Nunes", "Beatriz Lima", "Bruno Castro"]

# Mais similares a Bruno. Ele e deputado_b no par com Ana e deputado_a no par
# com Carla, entao esta lista exercita os dois lados do CASE.
SIMILARES_DE_BRUNO = [CARLA, ANA]

# Nos do grafo de 2024, na ordem alfabetica de nome que a consulta usa.
NOS_DO_GRAFO = [ALBERTO, ANA, BEATRIZ, BRUNO, CARLA]

# Arestas de 2024, na ordem (deputado_a, deputado_b) que a consulta usa.
ARESTAS_DO_GRAFO = [(ANA, BEATRIZ), (ANA, BRUNO), (ANA, CARLA), (ANA, ALBERTO)]


SQL = """
INSERT INTO app.deputado (deputado_id, nome, sigla_partido, sigla_uf, url_foto) VALUES
 (100, 'Ana Ribeiro',   'PT',   'SP', 'https://exemplo.test/ana.jpg'),
 (150, 'Beatriz Lima',  'PSOL', 'CE', 'https://exemplo.test/beatriz.jpg'),
 (200, 'Bruno Castro',  'PL',   'RJ', 'https://exemplo.test/bruno.jpg'),
 (300, 'Carla Dias',    'MDB',  'MG', 'https://exemplo.test/carla.jpg'),
 (400, 'Diego Alves',   'PP',   'BA', 'https://exemplo.test/diego.jpg'),
 (500, 'Elena Moraes',  'PSD',  'RS', 'https://exemplo.test/elena.jpg'),
 (600, 'Alberto Nunes', 'PSB',  'PE', 'https://exemplo.test/alberto.jpg');

-- O ano de app.votacao e coluna gerada a partir da data.
INSERT INTO app.votacao (votacao_id, data, sigla_orgao, descricao) VALUES
 ('v1', '2024-03-01', 'PLEN', 'Todos a favor'),
 ('v2', '2024-03-02', 'PLEN', 'Todos contra'),
 ('v3', '2024-03-03', 'PLEN', 'Nao contra Obstrucao'),
 ('v4', '2024-03-04', 'PLEN', 'Ana e Carla a favor, os demais contra'),
 ('v5', '2024-03-05', 'PLEN', 'Ana contra, os demais a favor'),
 ('v6', '2024-03-06', 'PLEN', 'Ana se absteve'),
 ('v7', '2024-03-07', 'PLEN', 'Bruno pelo Artigo 17'),
 ('v8', '2023-12-01', 'PLEN', 'Votacao do ano anterior');

-- Beatriz, Bruno e Alberto votam igual entre si, o que os deixa empatados em
-- 60.00 com Ana. O empate e de proposito: e o que o teste de desempate usa.
INSERT INTO app.voto (votacao_id, deputado_id, voto) VALUES
 ('v1', 100, 'Sim'),       ('v1', 150, 'Sim'),       ('v1', 200, 'Sim'),
 ('v1', 300, 'Sim'),       ('v1', 400, 'Sim'),       ('v1', 600, 'Sim'),
 ('v2', 100, 'Não'),       ('v2', 150, 'Não'),       ('v2', 200, 'Não'),
 ('v2', 300, 'Não'),       ('v2', 600, 'Não'),
 ('v3', 100, 'Não'),       ('v3', 150, 'Obstrução'), ('v3', 200, 'Obstrução'),
 ('v3', 600, 'Obstrução'),
 ('v4', 100, 'Sim'),       ('v4', 150, 'Não'),       ('v4', 200, 'Não'),
 ('v4', 300, 'Sim'),       ('v4', 600, 'Não'),
 ('v5', 100, 'Não'),       ('v5', 150, 'Sim'),       ('v5', 200, 'Sim'),
 ('v5', 600, 'Sim'),
 -- v6 e v7 ficam fora da conta pela RN01
 ('v6', 100, 'Abstenção'), ('v6', 200, 'Sim'),
 ('v7', 100, 'Sim'),       ('v7', 200, 'Artigo 17'),
 -- v8 e de outro ano
 ('v8', 100, 'Sim'),       ('v8', 200, 'Sim');

-- Tres execucoes. As duas primeiras sao do mesmo ano, e a de id maior e a que
-- os endpoints devem usar; a terceira existe para o ano aparecer em /anos
-- mesmo sem concordancia calculada.
INSERT INTO app.execucao
 (execucao_id, ano_inicio, ano_fim, minimo_votacoes_em_comum, k_vizinhos, concordancia_minima) VALUES
 (1, 2024, 2024, 3, 5, 75),
 (2, 2024, 2024, 3, 5, 75),
 (3, 2023, 2023, 3, 5, 75);
SELECT setval('app.execucao_execucao_id_seq', 3);

-- Execucao antiga: numeros errados de proposito. Se algum teste enxergar
-- 100.00 no par Ana/Bruno, o endpoint leu a execucao errada.
INSERT INTO app.concordancia
 (execucao_id, deputado_a, deputado_b, votacoes_em_comum, concordancias) VALUES
 (1, 100, 200, 5, 5);

-- Execucao atual: os numeros que decorrem dos votos acima.
INSERT INTO app.concordancia
 (execucao_id, deputado_a, deputado_b, votacoes_em_comum, concordancias) VALUES
 (2, 100, 150, 5, 3),
 (2, 100, 200, 5, 3),
 (2, 100, 300, 3, 3),
 (2, 100, 600, 5, 3),
 (2, 200, 300, 3, 2);

-- Os pesos abaixo divergem dos percentuais de proposito. Na vida real o peso
-- e o percentual arredondado, mas aqui eles diferem para provar que
-- listar_arestas devolve o percentual de app.concordancia, e nao o peso.
INSERT INTO app.aresta (execucao_id, deputado_a, deputado_b, peso) VALUES
 (1, 100, 200, 11),
 (2, 100, 150, 22),
 (2, 100, 200, 33),
 (2, 100, 300, 44),
 (2, 100, 600, 55);
"""
