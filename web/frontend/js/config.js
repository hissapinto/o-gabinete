/*
 * O Gabinete - Mapa de Similaridade Politica entre Deputados Federais
 * Arquivo: web/frontend/js/config.js
 *
 * Integrantes:
 *     Caio Ariel Cardoso Saraiva  - RA 10439611
 *     Isabela Hissa Pinto         - RA 10441873
 *     Kaique Barros Paiva         - RA 10441787
 *
 * Sintese:
 *     Endereco base da API, lido pelo js/dados.js. Script comum, carregado
 *     pelo index.html antes do js/app.js. O padrao /api serve aos dois
 *     ambientes sem build: no compose o nginx repassa /api/ para o backend,
 *     e no Render o rewrite do static site (render.yaml) faz o mesmo. So
 *     mude se a interface for servida sem esse repasse; ai use a URL completa
 *     da API e libere a origem em CORS_ORIGINS.
 */

window.GABINETE_API_BASE = '/api';
