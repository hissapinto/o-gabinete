/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/partidos.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Cores dos partidos. Todos os 20 partidos do grafo tem cor propria; as
 *     dez maiores bancadas sao as mais distintas entre si, e as menores sao
 *     afastadas de todas elas. Os valores moram no CSS (--partido-*), junto
 *     dos outros tokens do tema; aqui so fica o nome da variavel de cada um.
 *     Partido que ainda nao tem cor cai no cinza --partido-outro.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 *     29/10/2026 - Caio - Cores lidas das variaveis CSS; nova paleta.
 *     29/10/2026 - Caio - Cor propria para os 20 partidos; releitura na
 *                         troca de tema.
 */

// A cor segue o partido, e nao a posicao no ranking: trocar de ano nao
// repinta ninguem.
const VARIAVEIS = {
  PL: '--partido-pl',
  PT: '--partido-pt',
  'UNIÃO': '--partido-uniao',
  PP: '--partido-pp',
  MDB: '--partido-mdb',
  REPUBLICANOS: '--partido-republicanos',
  PSD: '--partido-psd',
  PDT: '--partido-pdt',
  PODE: '--partido-pode',
  PSB: '--partido-psb',
  PSOL: '--partido-psol',
  PSDB: '--partido-psdb',
  AVANTE: '--partido-avante',
  PCdoB: '--partido-pcdob',
  CIDADANIA: '--partido-cidadania',
  PRD: '--partido-prd',
  PV: '--partido-pv',
  SOLIDARIEDADE: '--partido-solidariedade',
  NOVO: '--partido-novo',
  REDE: '--partido-rede',
};

let cores = null;
let outro = null;

/** Rele as cores do CSS; chamado na troca de tema. */
export function lerCores() {
  const estilo = getComputedStyle(document.documentElement);
  cores = {};
  for (const [sigla, variavel] of Object.entries(VARIAVEIS)) {
    cores[sigla] = estilo.getPropertyValue(variavel).trim();
  }
  outro = estilo.getPropertyValue('--partido-outro').trim();
}

export function corDoPartido(sigla) {
  if (!cores) lerCores();
  return cores[sigla] ?? outro;
}

/** Partidos presentes nos nos, do maior para o menor: [{ sigla, total, cor }]. */
export function contarPartidos(nos) {
  const totais = new Map();
  for (const no of nos) {
    totais.set(no.sigla_partido, (totais.get(no.sigla_partido) ?? 0) + 1);
  }
  return [...totais]
    .map(([sigla, total]) => ({ sigla, total, cor: corDoPartido(sigla) }))
    .sort((a, b) => b.total - a.total || a.sigla.localeCompare(b.sigla, 'pt-BR'));
}

/** Cor de texto legivel sobre um fundo (branco ou tinta escura). */
export function tintaSobre(fundo) {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(fundo.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const luminancia = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminancia > 0.36 ? '#1b1f24' : '#ffffff';
}
