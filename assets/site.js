'use strict';
(() => {
  const form = document.querySelector('#source-filter');
  if (!form) return;
  const search = form.querySelector('#search');
  const principle = form.querySelector('#principle');
  const kind = form.querySelector('#kind');
  const cards = [...document.querySelectorAll('.source-card')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty-results');
  const params = new URLSearchParams(window.location.search);
  const normalize = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u0591-\u05c7]/g, '').trim();
  search.value = params.get('q') || '';
  if ([...principle.options].some(o => o.value === params.get('p'))) principle.value = params.get('p');
  if ([...kind.options].some(o => o.value === params.get('kind'))) kind.value = params.get('kind');
  const index = cards.map(card => ({card, text: normalize(card.dataset.search || card.textContent), principles: (card.dataset.principles || '').split(' '), kind: card.dataset.kind}));
  function apply() {
    const terms = normalize(search.value).split(/\s+/).filter(Boolean);
    let visible = 0;
    index.forEach(entry => {
      const show = terms.every(term => entry.text.includes(term)) && (!principle.value || entry.principles.includes(principle.value)) && (!kind.value || entry.kind === kind.value);
      entry.card.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = `${visible} מתוך ${cards.length} מקורות`;
    empty.hidden = visible !== 0;
    const next = new URLSearchParams();
    if (search.value.trim()) next.set('q', search.value.trim());
    if (principle.value) next.set('p', principle.value);
    if (kind.value) next.set('kind', kind.value);
    const query = next.toString();
    window.history.replaceState(null, '', window.location.pathname + (query ? '?' + query : '') + window.location.hash);
  }
  form.addEventListener('submit', event => event.preventDefault());
  search.addEventListener('input', apply);
  principle.addEventListener('change', apply);
  kind.addEventListener('change', apply);
  form.addEventListener('reset', () => { search.value = ''; principle.value = ''; kind.value = ''; apply(); });
  apply();
})();
