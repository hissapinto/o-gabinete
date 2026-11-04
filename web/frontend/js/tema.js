/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/tema.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Botao de tema claro/escuro. Sem escolha salva, segue o sistema
 *     (prefers-color-scheme) e acompanha se ele mudar; a escolha do usuario
 *     fica no localStorage. O tema inicial e aplicado por um script no
 *     <head> do index.html, antes do CSS, para nao piscar o tema errado;
 *     a chave do localStorage tem de ser a mesma dos dois lados.
 *
 * Historico de alteracoes:
 *     29/10/2026 - Caio - Criacao.
 */

const CHAVE = 'gabinete-tema';
const sistemaEscuro = window.matchMedia('(prefers-color-scheme: dark)');

// localStorage pode falhar (aba anonima, cookies bloqueados): sem ele, a
// escolha so vale ate recarregar a pagina.
function lerEscolha() {
  try {
    const valor = localStorage.getItem(CHAVE);
    return valor === 'claro' || valor === 'escuro' ? valor : null;
  } catch {
    return null;
  }
}

function salvarEscolha(tema) {
  try {
    localStorage.setItem(CHAVE, tema);
  } catch {
    // segue sem salvar
  }
}

export function temaAtual() {
  return document.documentElement.dataset.tema === 'escuro' ? 'escuro' : 'claro';
}

/** aoMudar(tema) e chamado depois de cada troca, para o grafo repintar. */
export function iniciarTema(aoMudar) {
  const botao = document.getElementById('alternar-tema');

  const aplicar = (tema) => {
    document.documentElement.dataset.tema = tema;
    const proximo = tema === 'escuro' ? 'claro' : 'escuro';
    const rotulo = `Ativar tema ${proximo}`;
    botao.setAttribute('aria-label', rotulo);
    botao.dataset.dica = rotulo;
    document.querySelector('meta[name="theme-color"]')
      .setAttribute('content', tema === 'escuro' ? '#171a1d' : '#ffffff');
    aoMudar(tema);
  };

  // sincroniza rotulo e meta com o tema que o <head> ja aplicou
  aplicar(temaAtual());

  botao.addEventListener('click', () => {
    const novo = temaAtual() === 'escuro' ? 'claro' : 'escuro';
    salvarEscolha(novo);
    aplicar(novo);
  });

  sistemaEscuro.addEventListener('change', (evento) => {
    if (lerEscolha() === null) aplicar(evento.matches ? 'escuro' : 'claro');
  });
}
