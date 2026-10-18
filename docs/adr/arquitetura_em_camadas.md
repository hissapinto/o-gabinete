# ADR-0001: Arquitetura em camadas com `grafo.txt` como fronteira

## Contexto

O projeto atende duas necessidades que puxam em direções opostas.

A disciplina de Teoria dos Grafos exige uma aplicação com menu de dez opções
construída sobre a classe de grafo apresentada em aula, com leitura e gravação
de um arquivo `grafo.txt` em formato especificado. O enunciado é explícito ao
dizer que a implementação como matriz ou lista de adjacência deve ser baseada
nessas classes.

Ao mesmo tempo, os dados vêm dos arquivos públicos de votação da Câmara dos
Deputados, cujo tratamento exige pandas, e o grupo quer entregar uma camada de
visualização em Pyvis e Streamlit para tornar o resultado compreensível ao
cidadão comum.

Juntar tudo em um único programa acoplaria a aplicação avaliada a bibliotecas
externas e a uma fonte de dados remota, com risco de a demonstração falhar por
motivo alheio ao que está sendo avaliado.

## Decisão

O sistema é dividido em camadas, com o arquivo `dados/grafo.txt` como fronteira
explícita entre o pipeline de dados e a aplicação.

```
O_Gabinete/
├── dados/
│   ├── brutos/                 CSVs baixados, não versionado
│   └── grafo.txt               camada de dados
├── docs/
│   ├── adr/                    registros de decisão
│   └── spikes/                 investigação descartável
├── grafos/                     aplicação de terminal
│   ├── apresentacao/           camada de apresentação
│   │   └── menu.py
│   ├── negocio/                camada de negócio
│   │   ├── grafo.py
│   │   └── logica_grafos.py
│   ├── persistencia/           camada de persistência
│   │   └── persistencia.py
│   └── main.py                 ponto de entrada
├── infra/db/init/              esquema do banco da versão web
├── pipeline/                   subsistema offline
│   ├── coleta.py
│   ├── processamento.py
│   ├── similaridade.py
│   ├── gerar_grafo.py
│   └── carga.py                grava o resultado no banco
├── tests/
├── web/                        versão web
│   ├── api/                    backend
│   └── frontend/               interface
├── docker-compose.yml
├── README.md
└── requirements.txt
```

| Camada | Módulo | Responsabilidade |
|---|---|---|
| Pipeline (subsistema offline) | `pipeline/coleta.py`, `pipeline/processamento.py`, `pipeline/similaridade.py`, `pipeline/gerar_grafo.py`, `pipeline/carga.py` | Baixar os CSVs, filtrar as votações de mérito, calcular a concordância, gerar o arquivo e carregar o banco |
| Apresentação | `grafos/apresentacao/menu.py`, `web/frontend/app.py` | Interação com o usuário |
| Negócio | `grafos/negocio/grafo.py`, `grafos/negocio/logica_grafos.py` | Estrutura do grafo e algoritmos |
| Persistência | `grafos/persistencia/persistencia.py` | Leitura e gravação do `grafo.txt` |
| Dados | `dados/grafo.txt` | Armazenamento |

`grafos/main.py` é o ponto de entrada e não pertence a nenhuma camada: monta as
peças e inicia a aplicação. Os arquivos em `docs/spikes/` também ficam fora das
camadas — são código descartável de investigação, preservado como evidência das
decisões tomadas, e nada no sistema os importa. `tests/` fica igualmente fora:
depende das camadas, mas nenhuma camada depende dele.

A dependência aponta sempre para baixo. As camadas são fechadas: a apresentação
não acessa a persistência diretamente.

Pandas e numpy existem somente no pipeline; Streamlit, somente em
`web/frontend/`; FastAPI e psycopg, somente em `web/api/`. As camadas de
negócio, persistência e apresentação da aplicação de terminal usam apenas a
biblioteca padrão do Python, de modo que ela continua executável sem instalar
dependências externas.

> **Nota de 18/10/2026.** A decisão registrada aqui não mudou. A árvore de
> diretórios e a tabela de módulos foram atualizadas para refletir a
> reorganização por componente (`src/` dividido em `grafos/` e `web/`) e a
> inclusão do banco de dados, registrada no
> [ADR-0002](introducao_banco_de_dados.md).