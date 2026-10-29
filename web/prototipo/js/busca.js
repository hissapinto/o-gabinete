/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/prototipo/js/busca.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Busca de deputado com autocomplete (UC02). Aceita nome, partido ou UF,
 *     ignora acentos e so deixa escolher quem existe no grafo, o que evita
 *     erro de digitacao. Segue o padrao combobox da WAI-ARIA: setas
 *     navegam, Enter escolhe, Esc fecha.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 */

import { el, normalizar } from './dom.js';
import { corDoPartido } from './partidos.js';

const MAX_SUGESTOES = 8;

let entrada, lista, botaoLimpar;
let deputados = [];
let sugestoes = [];
let ativa = -1;
let aoEscolher = () => {};
let aoLimpar = () => {};

export function iniciarBusca(eventos) {
  entrada = document.getElementById('busca');
  lista = document.getElementById('sugestoes');
  botaoLimpar = document.getElementById('busca-limpar');
  aoEscolher = eventos.aoEscolher;
  aoLimpar = eventos.aoLimpar;

  entrada.addEventListener('input', () => {
    botaoLimpar.hidden = entrada.value === '';
    atualizar();
  });
  entrada.addEventListener('focus', () => {
    if (entrada.value) {
      entrada.select();
      atualizar();
    }
  });
  entrada.addEventListener('keydown', teclar);
  entrada.addEventListener('blur', () => setTimeout(fechar, 120));
  botaoLimpar.addEventListener('click', () => {
    mostrarNome('');
    entrada.focus();
    aoLimpar();
  });
}

/** Deputados do ano carregado: [{ deputado_id, nome, sigla_partido, sigla_uf }]. */
export function definirDeputados(nos) {
  deputados = nos.map((no) => ({
    ...no,
    chaveNome: normalizar(no.nome),
    chaveCompleta: normalizar(`${no.nome} ${no.sigla_partido} ${no.sigla_uf} ${no.sigla_partido}-${no.sigla_uf}`),
  }));
}

/** Mostra o nome do deputado aberto na caixa de busca, como no esboco. */
export function mostrarNome(nome) {
  entrada.value = nome;
  botaoLimpar.hidden = nome === '';
  fechar();
}

export function focarBusca() {
  entrada.focus();
}

export function sugestoesAbertas() {
  return !lista.hidden;
}

function buscar(texto) {
  const termos = normalizar(texto).trim().split(/\s+/).filter(Boolean);
  if (termos.length === 0) return [];
  const consulta = termos.join(' ');

  const achados = [];
  for (const dep of deputados) {
    if (!termos.every((termo) => dep.chaveCompleta.includes(termo))) continue;
    // nome que comeca com o texto vem antes; depois, palavra do nome que
    // comeca com ele; por ultimo, o resto (partido, UF, meio de palavra)
    let peso = 3;
    if (dep.chaveNome.startsWith(consulta)) peso = 0;
    else if (dep.chaveNome.split(' ').some((p) => p.startsWith(termos[0]))) peso = 1;
    else if (dep.chaveNome.includes(termos[0])) peso = 2;
    achados.push({ dep, peso });
  }
  achados.sort((a, b) => a.peso - b.peso || a.dep.chaveNome.localeCompare(b.dep.chaveNome));
  return achados.map((a) => a.dep);
}

function atualizar() {
  const todos = buscar(entrada.value);
  sugestoes = todos.slice(0, MAX_SUGESTOES);
  ativa = sugestoes.length ? 0 : -1;
  lista.replaceChildren();

  if (!entrada.value.trim()) {
    fechar();
    return;
  }

  if (sugestoes.length === 0) {
    lista.append(el('li', { class: 'sugestao-vazia', role: 'presentation' },
      'Nenhum deputado encontrado. Tente parte do nome, o partido ou a UF.'));
  }

  sugestoes.forEach((dep, i) => {
    lista.append(el('li', {
      id: `sugestao-${i}`,
      role: 'option',
      class: 'sugestao',
      'aria-selected': i === ativa ? 'true' : 'false',
      onmousedown: (evento) => {
        evento.preventDefault(); // nao deixa o blur fechar antes do clique
        escolher(i);
      },
      onmousemove: () => marcar(i),
    },
    el('span', { class: 'ponto', style: { background: corDoPartido(dep.sigla_partido) }, 'aria-hidden': 'true' }),
    el('span', { class: 'sugestao-nome' }, ...destacar(dep.nome, entrada.value)),
    el('span', { class: 'sugestao-partido' }, `${dep.sigla_partido}-${dep.sigla_uf}`)));
  });

  if (todos.length > MAX_SUGESTOES) {
    lista.append(el('li', { class: 'sugestao-mais', role: 'presentation' },
      `+ ${todos.length - MAX_SUGESTOES} resultados. Continue digitando para refinar.`));
  }

  lista.hidden = false;
  entrada.setAttribute('aria-expanded', 'true');
  entrada.setAttribute('aria-activedescendant', ativa >= 0 ? `sugestao-${ativa}` : '');
}

/** Parte do nome que bate com o texto digitado, em negrito. */
function destacar(nome, texto) {
  const termo = normalizar(texto).trim().split(/\s+/)[0];
  const inicio = termo ? normalizar(nome).indexOf(termo) : -1;
  if (inicio < 0) return [nome];
  const fim = inicio + termo.length;
  return [nome.slice(0, inicio), el('mark', {}, nome.slice(inicio, fim)), nome.slice(fim)];
}

function marcar(i) {
  ativa = i;
  lista.querySelectorAll('[role="option"]').forEach((item, j) => {
    item.setAttribute('aria-selected', j === i ? 'true' : 'false');
    if (j === i) item.scrollIntoView({ block: 'nearest' });
  });
  entrada.setAttribute('aria-activedescendant', `sugestao-${i}`);
}

function teclar(evento) {
  const aberta = !lista.hidden && sugestoes.length > 0;
  if (evento.key === 'ArrowDown' && aberta) {
    evento.preventDefault();
    marcar((ativa + 1) % sugestoes.length);
  } else if (evento.key === 'ArrowUp' && aberta) {
    evento.preventDefault();
    marcar((ativa - 1 + sugestoes.length) % sugestoes.length);
  } else if (evento.key === 'Enter') {
    evento.preventDefault();
    if (aberta && ativa >= 0) escolher(ativa);
  } else if (evento.key === 'Escape' && !lista.hidden) {
    evento.stopPropagation(); // o primeiro Esc so fecha a lista
    fechar();
  }
}

function escolher(i) {
  const dep = sugestoes[i];
  mostrarNome(dep.nome);
  entrada.blur();
  aoEscolher(dep.deputado_id);
}

function fechar() {
  lista.hidden = true;
  entrada.setAttribute('aria-expanded', 'false');
  entrada.removeAttribute('aria-activedescendant');
}
