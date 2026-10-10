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

O sistema é dividido em camadas, com o arquivo `dados/grafos.txt` como fronteira
explícita entre o pipeline de dados e a aplicação.

```
O_Gabinete/
├── dados/
│   ├── brutos/                 CSVs baixados, não versionado
│   └── grafos.txt              camada de dados
├── docs/
│   ├── adr/                    registros de decisão
│   └── spikes/                 investigação descartável
├── grafos/
│   ├── apresentacao/           camada de apresentação
│   │   └── menu.py
│   ├── negocio/                camada de negócio
│   │   ├── grafo.py
│   │   └── logica_grafos.py
│   ├── persistencia/           camada de persistência
│   │   └── persistencia.py
│   └── main.py                 ponto de entrada
├── pipeline/                   subsistema offline
│   ├── coleta.py
│   ├── similaridade.py
│   └── gerar_grafo.py
├── tests/
├── web/
│   └── frontend/
│       └── app.py
├── README.md
└── requirements.txt
```

| Camada | Módulo | Responsabilidade |
|---|---|---|
| Pipeline (subsistema offline) | `pipeline/coleta.py`, `pipeline/similaridade.py`, `pipeline/gerar_grafo.py` | Baixar os CSVs, consultar a API, calcular similaridade, gerar o arquivo |
| Apresentação | `grafos/apresentacao/menu.py`, `web/frontend/app.py` | Interação com o usuário |
| Negócio | `grafos/negocio/grafo.py`, `grafos/negocio/logica_grafos.py` | Estrutura do grafo e algoritmos |
| Persistência | `grafos/persistencia/persistencia.py` | Leitura e gravação do `grafos.txt` |
| Dados | `dados/grafos.txt` | Armazenamento |

`grafos/main.py` é o ponto de entrada e não pertence a nenhuma camada: monta as
peças e inicia a aplicação. Os arquivos em `docs/spikes/` também ficam fora das
camadas — são código descartável de investigação, preservado como evidência das
decisões tomadas, e nada no sistema os importa. `tests/` fica igualmente fora:
depende das camadas, mas nenhuma camada depende dele.

A dependência aponta sempre para baixo. As camadas são fechadas: a apresentação
não acessa a persistência diretamente.

Pandas existe somente no pipeline. Streamlit, Pyvis e NetworkX existem somente
em `web/frontend/`; as camadas de negócio e persistência usam apenas a
biblioteca padrão do Python, de modo que a aplicação de terminal continua
executável sem instalar dependências externas.