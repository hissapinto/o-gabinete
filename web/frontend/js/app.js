/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/app.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Liga os modulos da tela. O estado visivel mora na URL (#2024 ou
 *     #2024/220593): o botao voltar do navegador funciona e da para mandar
 *     o link de um deputado especifico para quem for testar.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 *     29/10/2026 - Caio - Troca de tema, previa e aviso do partido
 *                         destacado pela legenda.
 *     29/10/2026 - Caio - Nao inicia em file:// (o index.html avisa).
 *     04/11/2026 - Caio - Copia do prototipo; a mensagem de erro cita a API.
 *     04/11/2026 - Caio - Aviso "Acordando o servidor" enquanto o dados.js
 *                         tenta de novo.
 */

import { aoEsperarServidor, carregarAnos, carregarDeputado, carregarGrafo } from './dados.js';
import { avisar, el, formatarNumero, formatarPercentual } from './dom.js';
import { contarPartidos, corDoPartido } from './partidos.js';
import * as grafo from './grafo.js';
import * as busca from './busca.js';
import * as painel from './painel.js';
import { iniciarTema } from './tema.js';

// Anos da 57a legislatura. Os que ainda nao tem grafo aparecem no seletor
// desabilitados, com "em breve", para o usuario saber que virao.
const ANOS_PREVISTOS = [2026, 2025, 2024, 2023];

const estado = {
  anos: [],          // anos com grafo, do /anos
  ano: null,         // ano desenhado
  dadosGrafo: null,
  porId: new Map(),  // deputado_id -> no
  faixa: null,       // { menor, maior } dos percentuais
  deputadoId: null,  // deputado aberto, ou null no grafo completo
  ficha: null,       // ficha mostrada no painel, para redesenhar na troca de tema
  partido: null,     // partido destacado na legenda
  pedido: 0,         // descarta respostas que chegam fora de ordem
};

const $ = (id) => document.getElementById(id);

const TEXTO_ACORDANDO = 'Acordando o servidor, isso pode levar até um minuto…';

// --- inicio ----------------------------------------------------------------

async function iniciar() {
  // Aberto direto do disco: o aviso do proprio index.html ja explica como
  // abrir; aqui so nao segue, para nao trocar o aviso pelo erro da API
  // (alguns navegadores rodam este modulo mesmo em file://).
  if (location.protocol === 'file:') return;

  if (typeof cytoscape === 'undefined') {
    mostrarErro('Não foi possível carregar o desenho do grafo',
      'O arquivo js/vendor/cytoscape.min.js não carregou. Recarregue a página; se continuar, confira se a pasta js/vendor foi copiada junto.',
      [{ texto: 'Recarregar', acao: () => location.reload() }]);
    return;
  }

  grafo.criarGrafo($('grafo'), {
    aoClicarNo: (id) => navegar(estado.ano, Number(id)),
    aoClicarFundo: () => {
      if (estado.deputadoId !== null) navegar(estado.ano, null);
      else if (estado.partido) escolherPartido(estado.partido);
    },
    aoPassarSobre: mostrarDica,
    aoSair: esconderDica,
  });
  iniciarTema(aoMudarTema);
  busca.iniciarBusca({
    aoEscolher: (id) => navegar(estado.ano, id),
    aoLimpar: () => navegar(estado.ano, null),
  });
  painel.iniciarPainel();

  $('seletor-ano').addEventListener('change', (e) => navegar(Number(e.target.value), null));
  $('voltar-grafo').addEventListener('click', () => navegar(estado.ano, null));
  $('zoom-mais').addEventListener('click', () => grafo.aproximar(1.35));
  $('zoom-menos').addEventListener('click', () => grafo.aproximar(1 / 1.35));
  $('zoom-ajustar').addEventListener('click', () => grafo.enquadrar());
  window.addEventListener('hashchange', rotear);
  document.addEventListener('keydown', teclar);
  aoEsperarServidor(mostrarAcordando);

  await carregarListaDeAnos();
}

async function carregarListaDeAnos() {
  mostrarCarregando('Carregando os anos disponíveis…');
  try {
    const resposta = await carregarAnos();
    estado.anos = resposta.anos.map((a) => a.ano);
  } catch (erro) {
    mostrarErro('Não foi possível carregar os dados',
      `${erro.message} A API não respondeu à lista de anos (/api/anos).`,
      [{ texto: 'Tentar novamente', acao: carregarListaDeAnos }]);
    return;
  }
  if (estado.anos.length === 0) {
    mostrarErro('Ainda não há grafo disponível', 'Nenhum ano foi processado até agora.', []);
    return;
  }
  preencherSeletorDeAnos();
  rotear();
}

function preencherSeletorDeAnos() {
  const anos = [...new Set([...ANOS_PREVISTOS, ...estado.anos])].sort((a, b) => b - a);
  $('seletor-ano').replaceChildren(...anos.map((ano) => {
    const disponivel = estado.anos.includes(ano);
    return el('option', { value: ano, disabled: !disponivel }, disponivel ? String(ano) : `${ano} · em breve`);
  }));
}

// --- navegacao -------------------------------------------------------------

/** Muda a URL; o hashchange chama rotear(). */
function navegar(ano, deputadoId) {
  const destino = deputadoId === null ? `#${ano}` : `#${ano}/${deputadoId}`;
  if (location.hash === destino) rotear();
  else location.hash = destino;
}

async function rotear() {
  const [anoTexto, idTexto] = location.hash.replace(/^#\/?/, '').split('/');
  const ano = Number(anoTexto) || estado.anos[0];
  const deputadoId = idTexto ? Number(idTexto) : null;

  $('seletor-ano').value = String(estado.anos.includes(ano) ? ano : estado.ano ?? estado.anos[0]);

  if (ano !== estado.ano) {
    const abriu = await abrirAno(ano);
    if (!abriu) return;
  }
  if (deputadoId !== null && !Number.isNaN(deputadoId)) await abrirDeputado(deputadoId);
  else fecharDeputado();
}

async function abrirAno(ano) {
  const pedido = ++estado.pedido;
  estado.deputadoId = null;

  if (!estado.anos.includes(ano)) {
    mostrarErro(`Ainda não há grafo para ${ano}`,
      `Os dados de ${ano} ainda não foram processados. Por enquanto, o ano disponível é ${estado.anos[0]}.`,
      [{ texto: `Abrir ${estado.anos[0]}`, acao: () => navegar(estado.anos[0], null) }]);
    estado.ano = null;
    return false;
  }

  mostrarCarregando(`Carregando o grafo de ${ano}…`);
  let dados;
  try {
    dados = await carregarGrafo(ano);
  } catch (erro) {
    if (pedido !== estado.pedido) return false;
    estado.ano = null;
    mostrarErro(`Não foi possível carregar o grafo de ${ano}`, erro.message,
      [{ texto: 'Tentar novamente', acao: () => { estado.ano = null; rotear(); } }]);
    return false;
  }
  if (pedido !== estado.pedido) return false;

  estado.ano = ano;
  estado.dadosGrafo = dados;
  estado.porId = new Map(dados.nos.map((no) => [no.deputado_id, no]));
  estado.partido = null;
  estado.faixa = grafo.desenhar(dados);
  busca.definirDeputados(dados.nos);
  document.title = `O Gabinete · ${ano}`;
  esconderEstado();

  if (dados.nos.length === 0) {
    mostrarErro(`O grafo de ${ano} está vazio`,
      'Ninguém teve votações em comum suficientes neste ano para entrar no grafo.', []);
  }
  return true;
}

async function abrirDeputado(deputadoId) {
  const no = estado.porId.get(deputadoId);
  if (!no) {
    avisar(`Deputado ${deputadoId} não está no grafo de ${estado.ano}.`);
    navegar(estado.ano, null);
    return;
  }

  const pedido = ++estado.pedido;
  estado.deputadoId = deputadoId;
  estado.partido = null;
  atualizarChipPartido();
  document.body.classList.add('modo-deputado');
  $('voltar-grafo').hidden = false;
  busca.mostrarNome(no.nome);
  painel.mostrarCarregandoDeputado(no, () => navegar(estado.ano, null));
  painel.abrirGaveta(true);
  grafo.focarDeputado(deputadoId, []);

  let ficha;
  try {
    ficha = await carregarDeputado(estado.ano, deputadoId);
  } catch (erro) {
    if (pedido !== estado.pedido) return;
    avisar(`Não foi possível abrir a ficha de ${no.nome}. ${erro.message}`);
    navegar(estado.ano, null);
    return;
  }
  if (pedido !== estado.pedido) return;

  // A tela mostra os 5 mais similares; a API real devolve 10 por padrao.
  estado.ficha = { ...ficha, mais_similares: ficha.mais_similares.slice(0, 5) };
  grafo.focarDeputado(deputadoId, estado.ficha.mais_similares);
  mostrarFicha();
  document.title = `${no.nome} · O Gabinete ${estado.ano}`;
}

function mostrarFicha() {
  painel.mostrarDeputado(estado.ficha, {
    aoVoltar: () => navegar(estado.ano, null),
    aoEscolher: (id) => navegar(estado.ano, id),
    aoRealcar: grafo.realcar,
  });
}

function fecharDeputado() {
  const estavaAberto = estado.deputadoId !== null || document.body.classList.contains('modo-deputado');
  estado.pedido++;
  estado.deputadoId = null;
  estado.ficha = null;
  document.body.classList.remove('modo-deputado');
  $('voltar-grafo').hidden = true;
  busca.mostrarNome('');
  if (estavaAberto) {
    painel.abrirGaveta(false);
    grafo.limparFoco();
  }
  if (estado.ano) document.title = `O Gabinete · ${estado.ano}`;
  mostrarPainelGeral();
  grafo.destacarPartido(estado.partido);
  atualizarChipPartido();
}

function mostrarPainelGeral() {
  if (!estado.dadosGrafo) return;
  painel.mostrarGeral({
    ano: estado.ano,
    grafo: estado.dadosGrafo,
    partidos: contarPartidos(estado.dadosGrafo.nos),
    faixa: estado.faixa,
    partidoAtivo: estado.partido,
    aoEscolherPartido: escolherPartido,
    aoPreverPartido: preverPartido,
  });
}

/** Clique na legenda: fixa o destaque do partido; clicar de novo desfaz. */
function escolherPartido(sigla) {
  estado.partido = estado.partido === sigla ? null : sigla;
  grafo.destacarPartido(estado.partido);
  painel.marcarPartido(estado.partido);
  atualizarChipPartido();
}

/** Mouse ou foco sobre a legenda: previa do destaque, se nenhum estiver fixado. */
function preverPartido(sigla) {
  if (estado.partido || estado.deputadoId !== null) return;
  grafo.destacarPartido(sigla);
}

/** Aviso sobre o grafo enquanto um partido esta destacado, com o x para desfazer. */
function atualizarChipPartido() {
  const chip = $('chip-partido');
  const sigla = estado.partido;
  if (!sigla || estado.deputadoId !== null) {
    chip.hidden = true;
    return;
  }
  const total = estado.dadosGrafo.nos.filter((n) => n.sigla_partido === sigla).length;
  chip.replaceChildren(
    el('span', { class: 'ponto', style: { background: corDoPartido(sigla) }, 'aria-hidden': 'true' }),
    el('span', {}, el('strong', {}, sigla), ` destacado · ${formatarNumero(total)} deputados`),
    el('button', {
      type: 'button',
      'aria-label': `Remover destaque de ${sigla}`,
      title: 'Remover destaque (Esc)',
      onclick: () => escolherPartido(sigla),
    }, '×'));
  chip.hidden = false;
}

/** Troca de tema: o grafo e o painel repintam com as cores do tema novo. */
function aoMudarTema() {
  grafo.aplicarTema();
  if (!estado.dadosGrafo) return;
  if (estado.ficha) mostrarFicha();
  else mostrarPainelGeral();
  atualizarChipPartido();
}

function teclar(evento) {
  const digitando = evento.target.matches('input, select, textarea');
  if (evento.key === 'Escape') {
    if (estado.deputadoId !== null) navegar(estado.ano, null);
    else if (estado.partido) escolherPartido(estado.partido);
  } else if (evento.key === '/' && !digitando) {
    evento.preventDefault();
    busca.focarBusca();
  }
}

// --- dica ao passar o mouse ------------------------------------------------

function mostrarDica(dados, posicao) {
  const dica = $('dica');
  dica.replaceChildren(...[
    el('strong', {}, dados.nome),
    el('span', { class: 'dica-partido' },
      el('span', { class: 'ponto', style: { background: corDoPartido(dados.partido) }, 'aria-hidden': 'true' }),
      `${dados.partido} · ${dados.uf}`),
    dados.posicao && el('span', { class: 'dica-similar' },
      `${dados.posicao}º mais similar · ${formatarPercentual(dados.similaridade)}`)].filter(Boolean));
  dica.hidden = false;
  const area = $('grafo').getBoundingClientRect();
  const largura = dica.offsetWidth;
  const x = Math.min(Math.max(posicao.x - largura / 2, 8), area.width - largura - 8);
  const acima = posicao.y - dica.offsetHeight - 16;
  dica.style.transform = `translate(${x}px, ${acima < 8 ? posicao.y + 18 : acima}px)`;
}

function esconderDica() {
  $('dica').hidden = true;
}

// --- carregando e erro -----------------------------------------------------

function mostrarCarregando(texto) {
  const caixa = $('estado');
  caixa.className = 'estado carregando';
  caixa.replaceChildren(
    el('div', { class: 'estado-cartao', role: 'status' },
      el('span', { class: 'giro', 'aria-hidden': 'true' }),
      el('p', { class: 'estado-texto' }, texto)));
  caixa.hidden = false;
}

/**
 * O dados.js esta tentando de novo. Se a tela esta no carregamento (anos ou
 * grafo), troca o texto do spinner; se ja ha grafo (abrindo uma ficha), avisa
 * sem cobrir o grafo. O erro so aparece depois que as tentativas acabam.
 */
function mostrarAcordando() {
  const caixa = $('estado');
  if (!caixa.hidden && caixa.classList.contains('carregando')) mostrarCarregando(TEXTO_ACORDANDO);
  else avisar(TEXTO_ACORDANDO);
}

function mostrarErro(tituloErro, detalhe, acoes) {
  const caixa = $('estado');
  caixa.className = 'estado erro';
  caixa.replaceChildren(
    el('div', { class: 'estado-cartao', role: 'alert' },
      el('span', { class: 'estado-icone', 'aria-hidden': 'true' }, '!'),
      el('h2', { class: 'estado-titulo' }, tituloErro),
      el('p', { class: 'estado-texto' }, detalhe),
      acoes.length > 0 && el('div', { class: 'estado-acoes' },
        acoes.map((a, i) => el('button', { type: 'button', class: i === 0 ? 'botao primario' : 'botao', onclick: a.acao }, a.texto)))));
  caixa.hidden = false;
}

function esconderEstado() {
  $('estado').hidden = true;
}

iniciar();
