/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/grafo.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Desenho do grafo com o Cytoscape.js. As posicoes vem prontas da API
 *     (layout preset), entao o grafo abre na hora e sempre igual. Este modulo
 *     so desenha e avisa interacoes; quem decide o que fazer e o app.js.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 *     29/10/2026 - Caio - Cores lidas do tema no CSS, nos maiores com
 *                         contorno mais fino e "Enquadrar grafo" no zoom.
 *     29/10/2026 - Caio - Modo deputado com contorno de 2px, numero em selo
 *                         e zoom limitado; troca de tema sem recarregar.
 *     05/11/2026 - Isabela - Faixa de similaridade fixa em 75-100% em todos
 *                            os anos, no lugar do minimo/maximo de cada ano.
 */

import { corDoPartido, lerCores } from './partidos.js';

const LARGURA_MIN = 0.6;
const LARGURA_MAX = 4.5;
// Faixa fixa de similaridade, igual em todos os anos: 75% e o criterio do
// pipeline (CONCORDANCIA_MINIMA) para existir aresta, e 100% e o teto.
const SIMILARIDADE_MIN = 75;
const SIMILARIDADE_MAX = 100;
// tamanho do texto dos rotulos na tela, em px, independente do zoom
const FONTE_ROTULO = 13;
const FONTE_SELO = 11;
const FONTE_GRAFO = 'Inter, system-ui, sans-serif';
// Zoom maximo ao abrir um deputado: mais que isso, os nos esmaecidos ao
// redor viram bolhas grandes e o contexto se perde.
const ZOOM_MAXIMO_FOCO = 1.3;

let cy = null;
let eventos = {};
let quadroPendente = false;

// O rotulo tem tamanho fixo na tela: dividido pelo zoom, porque o Cytoscape
// escala o texto junto com o grafo.
const naTela = (px) => () => px / cy.zoom();

/** Cores do grafo, lidas dos tokens --grafo-* do tema ativo no CSS. */
function lerTokens() {
  const estilo = getComputedStyle(document.documentElement);
  const token = (nome) => estilo.getPropertyValue(`--grafo-${nome}`).trim();
  return {
    aresta: token('aresta'),
    arestaOpacidade: Number(token('aresta-opacidade')),
    contorno: token('contorno'),
    contornoOpacidade: Number(token('contorno-opacidade')),
    contornoLargura: Number(token('contorno-largura')),
    destaque: token('destaque'),
    destaqueTinta: token('destaque-tinta'),
    rotuloFundo: token('rotulo-fundo'),
    rotuloTinta: token('rotulo-tinta'),
    rotuloBorda: token('rotulo-borda'),
    apagado: Number(token('apagado-opacidade')),
  };
}

// Posicoes possiveis do nome do deputado selecionado, na ordem de preferencia.
const LADOS = {
  acima: { valign: 'top', halign: 'center', mx: 0, my: -10 },
  abaixo: { valign: 'bottom', halign: 'center', mx: 0, my: 10 },
  direita: { valign: 'center', halign: 'right', mx: 10, my: 0 },
  esquerda: { valign: 'center', halign: 'left', mx: -10, my: 0 },
};

function montarEstilo(t) {
  return [
    {
      selector: 'node',
      style: {
        width: 26,
        height: 26,
        'background-color': 'data(cor)',
        'border-width': t.contornoLargura,
        'border-color': t.contorno,
        'border-opacity': t.contornoOpacidade,
        label: '',
        'transition-property': 'opacity, width, height, border-width',
        'transition-duration': 180,
      },
    },
    {
      selector: 'edge',
      style: {
        width: 'data(largura)',
        'line-color': t.aresta,
        opacity: t.arestaOpacidade,
        'curve-style': 'haystack',
        'haystack-radius': 0,
        'transition-property': 'opacity, line-color',
        'transition-duration': 180,
      },
    },
    {
      selector: 'node.sob-cursor',
      style: { 'border-width': 3, 'border-color': t.destaque, 'border-opacity': 1, 'z-index': 40 },
    },
    { selector: 'node.apagado', style: { opacity: t.apagado } },
    { selector: 'edge.apagado', style: { opacity: t.apagado / 4 } },
    {
      // Os mais similares levam o numero da posicao na lista do painel, como
      // as letras A-E do esboco: nome inteiro em cada um se sobreporia, porque
      // deputados parecidos ficam colados no desenho. O nome aparece na dica.
      // O numero e um selo no canto do no, na fonte da interface.
      selector: 'node.similar',
      style: {
        width: 28,
        height: 28,
        'border-width': 2,
        'border-color': t.destaque,
        'border-opacity': 1,
        label: 'data(rotulo)',
        color: t.destaqueTinta,
        'font-family': FONTE_GRAFO,
        'font-size': naTela(FONTE_SELO),
        'font-weight': 500,
        'text-valign': 'top',
        'text-halign': 'right',
        'text-margin-x': naTela(-6),
        'text-margin-y': naTela(6),
        'text-background-color': t.destaque,
        'text-background-opacity': 1,
        'text-background-padding': naTela(3),
        'text-background-shape': 'roundrectangle',
        'z-index': 20,
      },
    },
    {
      selector: 'node.similar.sob-cursor',
      style: { width: 34, height: 34, 'border-width': 2 },
    },
    {
      // O selecionado fica acima de tudo, com o nome sobre um fundo proprio,
      // para nenhum selo nem no vizinho cobrir o nome.
      selector: 'node.foco',
      style: {
        label: 'data(rotulo)',
        color: t.rotuloTinta,
        'font-family': FONTE_GRAFO,
        'font-size': naTela(FONTE_ROTULO + 1),
        'font-weight': 600,
        // do lado do no que nao cobre similares nem selos (ver ladoDoRotulo)
        'text-valign': (no) => LADOS[no.data('rotuloLado') ?? 'acima'].valign,
        'text-halign': (no) => LADOS[no.data('rotuloLado') ?? 'acima'].halign,
        'text-margin-x': (no) => LADOS[no.data('rotuloLado') ?? 'acima'].mx / cy.zoom(),
        'text-margin-y': (no) => LADOS[no.data('rotuloLado') ?? 'acima'].my / cy.zoom(),
        'text-background-color': t.rotuloFundo,
        'text-background-opacity': 1,
        'text-background-padding': naTela(5),
        'text-background-shape': 'roundrectangle',
        'text-border-color': t.rotuloBorda,
        'text-border-width': naTela(1),
        'text-border-opacity': 1,
        width: 38,
        height: 38,
        'border-width': 2,
        'border-color': t.destaque,
        'border-opacity': 1,
        'z-index': 50,
      },
    },
    {
      selector: 'edge.ligacao',
      style: { 'line-color': t.destaque, opacity: 0.9, 'z-index': 10 },
    },
    {
      // partido destacado pela legenda: acima dos esmaecidos e com contorno
      selector: 'node.do-partido',
      style: { 'border-width': 1.5, 'border-color': t.destaque, 'border-opacity': 0.9, 'z-index': 10 },
    },
    { selector: 'edge.do-partido', style: { opacity: Math.min(1, t.arestaOpacidade * 1.8) } },
  ];
}

/**
 * Cria o Cytoscape no container. eventos: { aoClicarNo(id), aoClicarFundo(),
 * aoPassarSobre(dados, posicaoNaTela), aoSair() }.
 */
export function criarGrafo(container, novosEventos) {
  eventos = novosEventos;
  cy = cytoscape({
    container,
    elements: [],
    style: montarEstilo(lerTokens()),
    layout: { name: 'preset' },
    minZoom: 0.15,
    maxZoom: 4,
    boxSelectionEnabled: false,
    autoungrabify: true,
    autounselectify: true,
    // nitidez: resolucao da tela (devicePixelRatio) e nada de trocar o
    // desenho por uma imagem durante zoom e arraste
    pixelRatio: 'auto',
    textureOnViewport: false,
    motionBlur: false,
  });

  cy.on('tap', 'node', (evento) => eventos.aoClicarNo(evento.target.id()));
  cy.on('tap', (evento) => {
    if (evento.target === cy) eventos.aoClicarFundo();
  });
  cy.on('mouseover', 'node', (evento) => {
    const no = evento.target;
    no.addClass('sob-cursor');
    container.style.cursor = 'pointer';
    eventos.aoPassarSobre(no.data(), no.renderedPosition());
  });
  cy.on('mouseout', 'node', (evento) => {
    evento.target.removeClass('sob-cursor');
    container.style.cursor = '';
    eventos.aoSair();
  });
  // o container muda de tamanho com a janela e com a gaveta do celular
  new ResizeObserver(() => cy.resize()).observe(container);

  cy.on('viewport', () => {
    eventos.aoSair();
    agendarAtualizacaoDosRotulos();
  });
}

function agendarAtualizacaoDosRotulos() {
  if (quadroPendente) return;
  quadroPendente = true;
  requestAnimationFrame(() => {
    quadroPendente = false;
    cy.nodes('.foco, .similar').updateStyle();
  });
}

/** Troca o grafo inteiro. A espessura da aresta segue a faixa fixa de 75% a 100%. */
export function desenhar(grafo) {
  const menor = SIMILARIDADE_MIN;
  const maior = SIMILARIDADE_MAX;
  const faixa = maior - menor;

  const nos = grafo.nos.map((no) => ({
    group: 'nodes',
    data: {
      id: String(no.deputado_id),
      nome: no.nome,
      rotulo: no.nome,
      partido: no.sigla_partido,
      uf: no.sigla_uf,
      cor: corDoPartido(no.sigla_partido),
    },
    position: { x: no.x ?? 0, y: no.y ?? 0 },
  }));
  const arestas = grafo.arestas.map((a) => ({
    group: 'edges',
    data: {
      id: `${a.deputado_a}-${a.deputado_b}`,
      source: String(a.deputado_a),
      target: String(a.deputado_b),
      percentual: Number(a.percentual),
      largura: LARGURA_MIN + ((Number(a.percentual) - menor) / faixa) * (LARGURA_MAX - LARGURA_MIN),
    },
  }));

  cy.elements().remove();
  cy.add([...nos, ...arestas]);
  cy.fit(undefined, margem());
  return { menor, maior };
}

function margem() {
  return window.innerWidth < 760 ? 24 : 48;
}

/** Modo deputado: o no aumentado, os similares rotulados, o resto esmaecido. */
export function focarDeputado(deputadoId, similares) {
  const foco = cy.getElementById(String(deputadoId));
  if (foco.empty()) return;
  cy.resize(); // a gaveta pode ter acabado de abrir; enquadra no tamanho atual

  let vizinhanca = foco;
  cy.batch(() => {
    limparClasses();
    cy.elements().addClass('apagado');
    foco.removeClass('apagado').addClass('foco');
    foco.data('rotulo', foco.data('nome'));

    similares.forEach((similar, i) => {
      const no = cy.getElementById(String(similar.deputado_id));
      if (no.empty()) return;
      no.removeClass('apagado').addClass('similar');
      no.data({ rotulo: String(i + 1), posicao: i + 1, similaridade: Number(similar.percentual) });
      foco.edgesWith(no).removeClass('apagado').addClass('ligacao');
      vizinhanca = vizinhanca.union(no);
    });
  });

  const destino = enquadramentoLimitado(vizinhanca);
  foco.data('rotuloLado', ladoDoRotulo(foco, vizinhanca.not(foco), destino.zoom));
  cy.stop(true, true);
  cy.animate(destino, { duration: 450, easing: 'ease-in-out-cubic' });
}

/**
 * Lado em que o nome do selecionado cobre menos similares e selos, contado
 * em pixels de tela no zoom final. Empate fica com o primeiro de LADOS.
 */
function ladoDoRotulo(foco, similares, zoom) {
  const largura = foco.data('nome').length * 7.5 + 16; // estimativa do texto + fundo
  const altura = 26;
  const raio = 19;
  const folga = 14; // raio de um similar ou de um selo
  const caixas = {
    acima: [0, -(raio + 10 + altura / 2)],
    abaixo: [0, raio + 10 + altura / 2],
    direita: [raio + 10 + largura / 2, 0],
    esquerda: [-(raio + 10 + largura / 2), 0],
  };
  const centro = foco.position();
  // centro de cada similar e do seu selo (canto de cima, a direita), na tela
  const pontos = [];
  similares.forEach((no) => {
    const x = (no.position().x - centro.x) * zoom;
    const y = (no.position().y - centro.y) * zoom;
    pontos.push([x, y], [x + 14, y - 14]);
  });

  let melhor = 'acima';
  let menos = Infinity;
  for (const [lado, [cx, cy0]] of Object.entries(caixas)) {
    const cobertos = pontos.filter(([x, y]) =>
      Math.abs(x - cx) < largura / 2 + folga && Math.abs(y - cy0) < altura / 2 + folga).length;
    if (cobertos < menos) {
      menos = cobertos;
      melhor = lado;
    }
  }
  return melhor;
}

/**
 * Zoom e posicao que mostram eles com folga larga, sem passar de
 * ZOOM_MAXIMO_FOCO. O fit do Cytoscape so tem o maxZoom global, alto
 * demais aqui, entao a conta e feita a mao.
 */
function enquadramentoLimitado(eles) {
  const caixa = eles.boundingBox({ includeLabels: false });
  const folga = window.innerWidth < 760 ? 48 : 140;
  const largura = Math.max(cy.width() - 2 * folga, 1);
  const altura = Math.max(cy.height() - 2 * folga, 1);
  const zoom = Math.min(
    ZOOM_MAXIMO_FOCO,
    caixa.w > 0 ? largura / caixa.w : Infinity,
    caixa.h > 0 ? altura / caixa.h : Infinity,
  );
  const centroX = (caixa.x1 + caixa.x2) / 2;
  const centroY = (caixa.y1 + caixa.y2) / 2;
  return {
    zoom,
    pan: { x: cy.width() / 2 - zoom * centroX, y: cy.height() / 2 - zoom * centroY },
  };
}

/** Destaca so os deputados de um partido (legenda clicavel). null limpa. */
export function destacarPartido(sigla) {
  cy.batch(() => {
    limparClasses();
    if (!sigla) return;
    const doPartido = cy.nodes().filter((no) => no.data('partido') === sigla);
    cy.elements().addClass('apagado');
    doPartido.removeClass('apagado').addClass('do-partido');
    doPartido.edgesWith(doPartido).removeClass('apagado').addClass('do-partido');
  });
}

/** Volta ao grafo completo, sem destaque, enquadrando tudo. */
export function limparFoco() {
  cy.batch(limparClasses);
  cy.resize();
  cy.stop();
  cy.animate({ fit: { eles: cy.elements(), padding: margem() } }, { duration: 400, easing: 'ease-in-out-cubic' });
}

function limparClasses() {
  cy.elements().removeClass('apagado foco similar ligacao do-partido');
  cy.nodes().removeData('posicao similaridade rotuloLado');
}

/** Realce passageiro de um no, ao passar o mouse num item do painel. */
export function realcar(deputadoId, ligado) {
  cy.getElementById(String(deputadoId)).toggleClass('sob-cursor', ligado);
}

/** Troca de tema: rele os tokens do CSS e repinta o grafo, sem recarregar. */
export function aplicarTema() {
  lerCores();
  cy.batch(() => {
    cy.nodes().forEach((no) => no.data('cor', corDoPartido(no.data('partido'))));
  });
  cy.style(montarEstilo(lerTokens()));
}

export function aproximar(fator) {
  // termina a animacao em curso antes, para cliques seguidos somarem
  cy.stop(true, true);
  const centro = { x: cy.width() / 2, y: cy.height() / 2 };
  cy.animate({ zoom: { level: cy.zoom() * fator, renderedPosition: centro } }, { duration: 200 });
}

/** Enquadrar grafo: o desenho inteiro na tela, com margem. */
export function enquadrar() {
  cy.stop(true, true);
  cy.animate({ fit: { eles: cy.elements(), padding: margem() } }, { duration: 350, easing: 'ease-in-out-cubic' });
}
