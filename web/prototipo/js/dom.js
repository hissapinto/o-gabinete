/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/prototipo/js/dom.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Utilitarios de DOM e de texto compartilhados pelos modulos da tela.
 *     Texto vindo dos dados entra sempre como textContent, nunca como HTML.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao, para o prototipo da Parte 3 de IHC.
 */

/** el('div', { class: 'x', onclick: fn }, 'texto', filho) */
export function el(tag, atributos = {}, ...filhos) {
  const elemento = document.createElement(tag);
  for (const [chave, valor] of Object.entries(atributos)) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (chave.startsWith('on')) {
      elemento.addEventListener(chave.slice(2), valor);
    } else if (chave === 'style') {
      Object.assign(elemento.style, valor);
    } else {
      elemento.setAttribute(chave, valor === true ? '' : valor);
    }
  }
  for (const filho of filhos.flat()) {
    if (filho === null || filho === undefined || filho === false) continue;
    elemento.append(filho instanceof Node ? filho : document.createTextNode(String(filho)));
  }
  return elemento;
}

/** Sem acento e em minusculas, para comparar nomes. */
export function normalizar(texto) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export function iniciais(nome) {
  const partes = nome.split(/\s+/).filter((p) => /^[\p{L}]/u.test(p));
  if (partes.length === 0) return '?';
  const primeira = partes[0][0];
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : '';
  return (primeira + ultima).toUpperCase();
}

const numero = new Intl.NumberFormat('pt-BR');
const decimal = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

export const formatarNumero = (n) => numero.format(n);
export const formatarPercentual = (p) => `${decimal.format(Number(p))}%`;

let temporizadorAviso;

/** Mensagem curta no rodape da tela, que some sozinha. */
export function avisar(mensagem) {
  const aviso = document.getElementById('aviso');
  aviso.textContent = mensagem;
  aviso.classList.add('visivel');
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => aviso.classList.remove('visivel'), 4500);
}
