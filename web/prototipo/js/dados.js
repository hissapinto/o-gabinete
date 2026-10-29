/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/prototipo/js/dados.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Unico modulo que acessa dados. Os JSONs estaticos em dados/ seguem as
 *     rotas e o formato da API (web/api/rotas). Para ler a API real, troque
 *     BASE pela URL dela e deixe SUFIXO vazio; nada mais muda.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 */

const BASE = 'dados';   // API real: 'http://localhost:8000'
const SUFIXO = '.json'; // API real: ''

export class ErroDados extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.status = status;
  }
}

// cada recurso e baixado uma vez so; o mesmo pedido devolve a mesma promessa
const cache = new Map();

function buscar(caminho) {
  if (!cache.has(caminho)) {
    const pedido = fetch(`${BASE}${caminho}${SUFIXO}`)
      .catch(() => {
        throw new ErroDados('Sem conexão com o servidor de dados.', 0);
      })
      .then((resposta) => {
        if (resposta.status === 404) {
          throw new ErroDados('Os dados pedidos não foram encontrados.', 404);
        }
        if (!resposta.ok) {
          throw new ErroDados(`O servidor respondeu com erro ${resposta.status}.`, resposta.status);
        }
        return resposta.json();
      });
    // falha nao fica no cache: "tentar novamente" precisa pedir de novo
    pedido.catch(() => cache.delete(caminho));
    cache.set(caminho, pedido);
  }
  return cache.get(caminho);
}

/** GET /anos -> { anos: [{ ano }] }, do mais recente ao mais antigo. */
export function carregarAnos() {
  return buscar('/anos');
}

/** GET /anos/{ano}/grafo -> { ano, nos: [...], arestas: [...] }. */
export function carregarGrafo(ano) {
  return buscar(`/anos/${ano}/grafo`);
}

/** GET /anos/{ano}/deputados/{id} -> { ano, deputado, mais_similares }. */
export function carregarDeputado(ano, deputadoId) {
  return buscar(`/anos/${ano}/deputados/${deputadoId}`);
}
