/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/dados.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Unico modulo que acessa dados. Le a API do grupo (web/api/rotas) a
 *     partir de window.GABINETE_API_BASE (js/config.js), por padrao /api: o
 *     proxy do nginx no compose e o rewrite do static site no Render, ambos
 *     na mesma origem da pagina, sem CORS. O web/prototipo/ le os mesmos
 *     caminhos em JSONs estaticos; o formato das respostas e o mesmo.
 *
 *     Servidor dormindo (API do Render hibernada, Neon suspenso): falha de
 *     rede, tempo esgotado, 502/503/504 ou resposta que nao e JSON (a pagina
 *     de "acordando" do Render) sao tentadas de novo, com espera crescente,
 *     por ate ~90 s. Na primeira dessas falhas, avisa quem se inscreveu em
 *     aoEsperarServidor, para a tela trocar o texto de carregamento.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 *     04/11/2026 - Caio - Copia do prototipo lendo a API pelo proxy /api/;
 *                         a ficha pede so os 5 mais similares que a tela usa.
 *     04/11/2026 - Caio - BASE lida do js/config.js e novas tentativas
 *                         enquanto o servidor acorda.
 */

// js/config.js define a base; /api e o proxy do nginx e o rewrite do Render
const BASE = window.GABINETE_API_BASE ?? '/api';
// a tela mostra os 5 mais similares (app.js); a API devolve 10 por padrao
const LIMITE_SIMILARES = 5;

export class ErroDados extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.status = status;
  }
}

// --- servidor acordando -------------------------------------------------------

// Quanto tempo insistir antes de mostrar o erro: a API gratuita do Render
// leva cerca de um minuto para acordar.
const ESPERA_MAXIMA_MS = 90_000;
// Tempo de cada tentativa, para um pedido preso nao gastar a espera toda.
const TEMPO_POR_TENTATIVA_MS = 20_000;
// Espera entre tentativas, crescente; a ultima se repete.
const ESPERAS_MS = [1_000, 2_000, 4_000, 8_000, 15_000];
// Erros HTTP de servidor fora do ar ou acordando. 500 e 404 nao entram: sao
// respostas reais da API e nao melhoram tentando de novo.
const STATUS_PASSAGEIROS = new Set([502, 503, 504]);

class ErroPassageiro extends ErroDados {}

const inscritos = new Set();

/** fn() e chamada quando um pedido falha de um jeito que vale esperar. */
export function aoEsperarServidor(fn) {
  inscritos.add(fn);
}

const dormir = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

/** Uma tentativa: devolve o JSON ou lanca ErroDados (ErroPassageiro se vale insistir). */
async function tentar(url, tempo) {
  const controle = new AbortController();
  const relogio = setTimeout(() => controle.abort(), tempo);
  let resposta;
  try {
    resposta = await fetch(url, { signal: controle.signal });
  } catch {
    throw new ErroPassageiro('Sem conexão com o servidor de dados.', 0);
  } finally {
    clearTimeout(relogio);
  }
  if (resposta.status === 404) {
    throw new ErroDados('Os dados pedidos não foram encontrados.', 404);
  }
  if (STATUS_PASSAGEIROS.has(resposta.status)) {
    throw new ErroPassageiro(`O servidor respondeu com erro ${resposta.status}.`, resposta.status);
  }
  if (!resposta.ok) {
    throw new ErroDados(`O servidor respondeu com erro ${resposta.status}.`, resposta.status);
  }
  try {
    return await resposta.json();
  } catch {
    // ex.: a pagina HTML que o Render mostra enquanto a API acorda
    throw new ErroPassageiro('O servidor respondeu algo que não é dado (ainda acordando?).', resposta.status);
  }
}

/** Tenta de novo os erros passageiros, com espera crescente, ate ESPERA_MAXIMA_MS. */
async function pedirComPaciencia(url) {
  const limite = Date.now() + ESPERA_MAXIMA_MS;
  for (let vez = 0; ; vez++) {
    const restante = limite - Date.now();
    try {
      return await tentar(url, Math.max(1_000, Math.min(TEMPO_POR_TENTATIVA_MS, restante)));
    } catch (erro) {
      if (!(erro instanceof ErroPassageiro)) throw erro;
      const espera = ESPERAS_MS[Math.min(vez, ESPERAS_MS.length - 1)];
      if (Date.now() + espera >= limite) {
        throw new ErroDados(`${erro.message} O servidor não respondeu em ${ESPERA_MAXIMA_MS / 1000} s.`, erro.status);
      }
      if (vez === 0) inscritos.forEach((fn) => fn());
      await dormir(espera);
    }
  }
}

// --- leitura -------------------------------------------------------------------

// cada recurso e baixado uma vez so; o mesmo pedido devolve a mesma promessa
const cache = new Map();

function buscar(caminho) {
  if (!cache.has(caminho)) {
    const pedido = pedirComPaciencia(`${BASE}${caminho}`);
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

/** GET /anos/{ano}/deputados/{id}?limite=5 -> { ano, deputado, mais_similares }. */
export function carregarDeputado(ano, deputadoId) {
  return buscar(`/anos/${ano}/deputados/${deputadoId}?limite=${LIMITE_SIMILARES}`);
}
