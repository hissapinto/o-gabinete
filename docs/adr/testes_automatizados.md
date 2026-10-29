# ADR-0003: Testes automatizados da API contra banco real, com integração contínua

## Status

Aceito — 21/10/2026

Autores: Caio Ariel Cardoso Saraiva, Isabela Hissa Pinto, Kaique Barros Paiva

## Contexto

A API chegou a seis rotas, e a lógica que decide o que a interface mostra está
majoritariamente **em SQL**, não em Python: a regra de concordância RN01, que
trata Obstrução como voto contra e deixa Abstenção e Artigo 17 fora da conta; o
`CASE` que devolve "o outro" do par, já que o banco guarda cada par uma vez só,
com o menor id em `deputado_a`; o `JOIN` que faz a aresta mostrar o percentual
de `app.concordancia` em vez do peso de `app.aresta`.

Erros nesses pontos não derrubam a aplicação. Eles devolvem **números errados,
em silêncio** — uma lista de similares faltando metade dos pares, uma aresta com
o percentual de outra tabela, uma votação contada como divergência quando a RN01
diz o contrário. São exatamente os defeitos que uma demonstração não revela e
que um revisor não pega lendo o diff.

Agrava isso o fato de a RN01 existir em **dois lugares**: em
`pipeline/similaridade.py`, que calcula os contadores gravados no banco, e em
`web/api/repositorios/voto.py`, que lista as votações por trás desses
contadores. Se as duas implementações divergirem, a tela passa a mostrar uma
lista que não bate com o percentual exibido ao lado dela, e nenhum erro aparece.

Testes com dublês do banco verificariam o Python que envolve as consultas, e não
as consultas — ou seja, tudo menos o que corre risco.

## Decisão

Uma suíte em **pytest**, em `web/api/tests/`, que roda contra um **PostgreSQL de
verdade**, e um workflow do **GitHub Actions** que a executa a cada push e a
cada pull request.

A pasta de testes espelha as camadas da API, de modo que cada arquivo de teste
tenha um arquivo de código correspondente:

| Camada | Verifica | Como |
|---|---|---|
| `tests/repositorios/` | o SQL | consultas reais contra o banco |
| `tests/servicos/` | as regras de decisão | qual entrada dá 404, qual dá lista vazia, qual execução é escolhida |
| `tests/rotas/` | a tradução para HTTP | `TestClient` do FastAPI, status e validação de parâmetros |

A cada execução a suíte apaga e recria um banco separado, por padrão
`gabinete_teste`, aplica nele o mesmo `infra/db/init/01-schema.sql` que o
container usa e grava o cenário de `tests/cenario.py`. O banco de
desenvolvimento não é tocado, e nenhum dado do `carga.py` é necessário.

O cenário é pequeno e deliberado — sete deputados e oito votações —, montado
para cobrir as armadilhas da RN01 e os desfechos de cada endpoint, incluindo
duas execuções no mesmo ano, para provar que vale a mais recente, e três
deputados empatados em percentual, para provar o desempate por nome.

Na integração contínua o PostgreSQL sobe como serviço do próprio job, com
`healthcheck`. O job não acessa a internet nem o Portal da Câmara: roda em
segundos e não falha por indisponibilidade de terceiros.

## Alternativas consideradas

**Dublês do banco (mocks).** Rápidos e sem infraestrutura. Descartada porque não
exercitam o SQL, que é onde mora o risco: um `CASE` invertido ou um `JOIN` na
coluna errada passaria em todos os testes.

**SQLite em memória.** Mais leve que subir o PostgreSQL. Descartada por diferença
de dialeto. O esquema usa coluna gerada (`percentual`), e as consultas usam
`FILTER`, `ANY(%s)` e `LIMIT NULL`; um teste que passasse no SQLite não diria
nada sobre o comportamento em produção, e pior, poderia esconder um erro real.

**Testar apenas pelas rotas.** Menos arquivos e cobertura parecida. Descartada
porque uma falha não diria qual camada errou — a mesma asserção quebrada pode
significar SQL errado, regra errada ou status errado.

## Consequências

**Positivas**

- Uma alteração no SQL que mude o resultado quebra a suíte antes de chegar à `main`.
- O teste `test_as_duas_listas_somam_as_votacoes_em_comum` compara a regra da API
  com o contador gravado pelo pipeline, e é o único ponto do projeto que
  verificaria a divergência entre as duas implementações da RN01.
- A suíte é a documentação executável do contrato: cada desfecho de cada rota
  está escrito como um teste com nome em português.
- O selo no README mostra o estado real da `main` a qualquer momento.

**Custos**

- Rodar os testes exige um PostgreSQL acessível; sem ele a suíte para com uma
  instrução, em vez de falhar teste a teste.
- O cenário de `tests/cenario.py` precisa ser mantido junto com o
  `01-schema.sql`: mudança de esquema quebra a suíte inteira de uma vez.
- Os testes de repositório são acoplados ao PostgreSQL por construção, e não
  sobreviveriam a uma troca de banco — custo aceito conscientemente, já que a
  decisão pelo PostgreSQL está registrada no [ADR-0002](introducao_banco_de_dados.md).

## Verificação

A suíte foi submetida a teste de mutação antes de ser aceita: sete defeitos
foram introduzidos de propósito no código, um de cada vez, e seis falharam na
primeira tentativa. O sétimo — trocar o desempate por nome pelo id — passou,
revelando falha no cenário, que tinha apenas dois deputados empatados; com dois,
a ordem alfabética coincide com a ordem por id ou com o seu inverso. O cenário
foi refeito com três empatados, e a mutação passou a ser detectada nos dois
sentidos.
