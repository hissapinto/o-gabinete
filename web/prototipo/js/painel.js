/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/prototipo/js/painel.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Painel lateral (gaveta embaixo, no celular). Dois conteudos: o geral,
 *     com legenda clicavel e estatisticas do ano, e o do deputado, com foto,
 *     partido/UF e a lista dos mais similares.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 *     29/10/2026 - Caio - Legenda com todos os partidos, cada um com cor
 *                         propria, e previa do destaque ao passar o mouse.
 */

import { el, formatarNumero, formatarPercentual, iniciais } from './dom.js';
import { corDoPartido, tintaSobre } from './partidos.js';

const conteudo = () => document.getElementById('painel-conteudo');
const titulo = () => document.getElementById('painel-titulo');

let botoesPartido = new Map();
let legenda = null;

// --- gaveta (celular) ------------------------------------------------------

export function iniciarPainel() {
  const alca = document.getElementById('painel-alca');
  alca.addEventListener('click', () => abrirGaveta(!document.body.classList.contains('gaveta-aberta')));
}

export function abrirGaveta(aberta) {
  document.body.classList.toggle('gaveta-aberta', aberta);
  document.getElementById('painel-alca').setAttribute('aria-expanded', String(aberta));
}

// --- conteudo geral --------------------------------------------------------

/**
 * Legenda e estatisticas do ano. partidos vem de contarPartidos();
 * faixa e { menor, maior } dos percentuais das arestas.
 */
export function mostrarGeral({ ano, grafo, partidos, faixa, partidoAtivo, aoEscolherPartido, aoPreverPartido }) {
  titulo().textContent = `Legenda e estatísticas · ${ano}`;
  botoesPartido = new Map();

  // Clique fixa o destaque; passar o mouse (ou focar pelo teclado) mostra
  // uma previa enquanto nenhum partido esta fixado.
  const botao = (p) => {
    const b = el('button', {
      type: 'button',
      class: 'legenda-item',
      'aria-pressed': p.sigla === partidoAtivo ? 'true' : 'false',
      'aria-label': `${p.sigla}, ${p.total} deputados. Destacar no grafo`,
      onclick: () => aoEscolherPartido(p.sigla),
      onmouseenter: () => aoPreverPartido(p.sigla),
      onmouseleave: () => aoPreverPartido(null),
      onfocus: () => aoPreverPartido(p.sigla),
      onblur: () => aoPreverPartido(null),
    },
    el('span', { class: 'ponto', style: { background: p.cor }, 'aria-hidden': 'true' }),
    el('span', { class: 'legenda-sigla' }, p.sigla),
    el('span', { class: 'legenda-total' }, formatarNumero(p.total)));
    botoesPartido.set(p.sigla, b);
    return b;
  };

  conteudo().replaceChildren(
    el('section', { class: 'bloco' },
      el('h2', { class: 'bloco-titulo' }, 'Estatísticas'),
      el('dl', { class: 'numeros' },
        numero('Deputados', formatarNumero(grafo.nos.length)),
        numero('Conexões', formatarNumero(grafo.arestas.length)),
        numero('Ano', String(ano)),
        numero('Similaridade', grafo.arestas.length
          ? `${Math.round(faixa.menor)}–${Math.round(faixa.maior)}%` : '—')),
      el('p', { class: 'fonte' },
        'Fonte: votações nominais do ',
        el('a', { href: 'https://dadosabertos.camara.leg.br', target: '_blank', rel: 'noopener' },
          'Portal de Dados Abertos da Câmara dos Deputados'),
        '.')),

    el('section', { class: 'bloco' },
      el('div', { class: 'bloco-cabecalho' },
        el('h2', { class: 'bloco-titulo' }, 'Partidos'),
        el('span', { class: 'bloco-dica' }, 'clique para destacar')),
      legenda = el('div', { class: partidoAtivo ? 'legenda com-destaque' : 'legenda' }, partidos.map(botao))),

    el('section', { class: 'bloco' },
      el('h2', { class: 'bloco-titulo' }, 'Como ler o grafo'),
      el('ul', { class: 'como-ler' },
        el('li', {}, el('span', { class: 'icone-no', 'aria-hidden': 'true' }),
          'Cada ponto é um deputado, na cor do partido.'),
        el('li', {}, el('span', { class: 'icone-linhas', 'aria-hidden': 'true' },
          el('i', { class: 'fina' }), el('i', { class: 'grossa' })),
          `Uma linha liga deputados que votaram de forma parecida. Quanto mais grossa, mais parecidos (de ${Math.round(faixa.menor)}% a ${Math.round(faixa.maior)}%).`),
        el('li', {}, el('span', { class: 'icone-clique', 'aria-hidden': 'true' }),
          'Clique num ponto ou busque um nome para ver os deputados mais parecidos com ele.'))),
  );
}

function numero(rotulo, valor) {
  return el('div', { class: 'numero' }, el('dt', {}, rotulo), el('dd', {}, valor));
}

/** Marca o partido destacado na legenda sem redesenhar o painel. */
export function marcarPartido(sigla) {
  for (const [s, botao] of botoesPartido) {
    botao.setAttribute('aria-pressed', s === sigla ? 'true' : 'false');
  }
  legenda?.classList.toggle('com-destaque', Boolean(sigla));
}

// --- conteudo do deputado --------------------------------------------------

/** Esqueleto enquanto a ficha carrega, com o que o grafo ja sabe. */
export function mostrarCarregandoDeputado(no, aoVoltar) {
  titulo().textContent = no.nome;
  conteudo().replaceChildren(
    botaoVoltar(aoVoltar),
    el('div', { class: 'ficha', 'aria-busy': 'true' },
      avatar(no.nome, no.sigla_partido, null),
      el('div', { class: 'ficha-texto' },
        el('h2', { class: 'ficha-nome' }, no.nome),
        partidoUf(no.sigla_partido, no.sigla_uf))),
    el('div', { class: 'esqueleto' }, [1, 2, 3, 4, 5].map(() => el('span'))),
  );
}

/**
 * Ficha do deputado (formato de GET /anos/{ano}/deputados/{id}).
 * eventos: { aoVoltar, aoEscolher(id), aoRealcar(id, ligado) }
 */
export function mostrarDeputado(ficha, { aoVoltar, aoEscolher, aoRealcar }) {
  const { deputado, mais_similares: similares, ano } = ficha;
  titulo().textContent = deputado.nome;

  const lista = similares.length === 0
    ? el('p', { class: 'vazio' },
      `${deputado.nome} votou em ${ano}, mas teve poucas votações em comum com os demais para entrar no grafo.`)
    : el('ol', { class: 'similares' }, similares.map((s, i) => el('li', {},
      el('button', {
        type: 'button',
        class: 'similar',
        onclick: () => aoEscolher(s.deputado_id),
        onmouseenter: () => aoRealcar(s.deputado_id, true),
        onmouseleave: () => aoRealcar(s.deputado_id, false),
        onfocus: () => aoRealcar(s.deputado_id, true),
        onblur: () => aoRealcar(s.deputado_id, false),
        'aria-label': `${s.nome}, ${s.sigla_partido}, ${formatarPercentual(s.percentual)} de concordância. Abrir.`,
      },
      el('span', { class: 'similar-posicao', 'aria-hidden': 'true' }, String(i + 1)),
      el('span', { class: 'similar-corpo' },
        el('span', { class: 'similar-linha' },
          el('span', { class: 'similar-nome' }, s.nome),
          el('span', { class: 'similar-pct' }, formatarPercentual(s.percentual))),
        el('span', { class: 'similar-linha similar-detalhe' },
          el('span', { class: 'ponto', style: { background: corDoPartido(s.sigla_partido) }, 'aria-hidden': 'true' }),
          s.sigla_partido),
        el('span', { class: 'barra', 'aria-hidden': 'true' },
          el('span', { style: { width: `${Number(s.percentual)}%` } }))),
      el('span', { class: 'similar-seta', 'aria-hidden': 'true' }, '›')))));

  conteudo().replaceChildren(
    botaoVoltar(aoVoltar),
    el('div', { class: 'ficha' },
      avatar(deputado.nome, deputado.sigla_partido, deputado.url_foto),
      el('div', { class: 'ficha-texto' },
        el('h2', { class: 'ficha-nome' }, deputado.nome),
        partidoUf(deputado.sigla_partido, deputado.sigla_uf),
        el('p', { class: 'ficha-ano' }, `Votações nominais de ${ano}`))),
    el('section', { class: 'bloco' },
      el('div', { class: 'bloco-cabecalho' },
        el('h2', { class: 'bloco-titulo' }, 'Mais similares'),
        el('span', { class: 'bloco-dica' }, 'clique para abrir')),
      lista,
      similares.length > 0 && el('p', { class: 'nota' },
        'Percentual de votações em que os dois votaram do mesmo jeito (Sim, ou Não/Obstrução).')),
  );
}

function botaoVoltar(aoVoltar) {
  return el('button', { type: 'button', class: 'voltar', onclick: aoVoltar },
    el('span', { 'aria-hidden': 'true' }, '←'), ' Voltar ao grafo completo',
    el('kbd', {}, 'Esc'));
}

function partidoUf(partido, uf) {
  return el('p', { class: 'ficha-partido' },
    el('span', { class: 'ponto', style: { background: corDoPartido(partido) }, 'aria-hidden': 'true' }),
    `${partido} · ${uf}`);
}

/** Foto da Camara; sem URL ou se a imagem falhar, um avatar com as iniciais. */
function avatar(nome, partido, url) {
  const cor = corDoPartido(partido);
  const comIniciais = () => el('span', {
    class: 'avatar avatar-iniciais',
    style: { background: cor, color: tintaSobre(cor) },
    role: 'img',
    'aria-label': `Sem foto de ${nome}`,
  }, iniciais(nome));

  if (!url) return comIniciais();
  const imagem = el('img', {
    class: 'avatar',
    src: url,
    alt: `Foto de ${nome}`,
    referrerpolicy: 'no-referrer',
    style: { borderColor: cor },
  });
  imagem.addEventListener('error', () => imagem.replaceWith(comIniciais()), { once: true });
  return imagem;
}
