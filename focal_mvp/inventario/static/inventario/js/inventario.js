/*! FOCAL - inventario.js (sin HUB/TABS)
   - Highlight de fila recién agregada
   - Modal descontar
   - Stepper cantidad
   - Fade de alerts (toasts siguen en CSS)
   - Asistente flotante
*/
(function () {
  'use strict';

  // Helpers
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => r.querySelectorAll(s);
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  // ========= HIGHLIGHT fila recién agregada =========
  (function highlightNewRow() {
    const params  = new URLSearchParams(location.search);
    const metaHL  = document.querySelector('meta[name="highlight-sku"]');
    const fromQS  = (params.get('hl') || '').trim();
    const fromMeta = metaHL ? (metaHL.getAttribute('content') || '').trim() : '';
    const skuToHL = fromMeta || fromQS;
    if (!skuToHL) return;

    const tbody = $('#tablaInventario tbody');
    if (!tbody) return;
    const row = tbody.querySelector(`tr[data-sku="${CSS.escape(skuToHL)}"]`);
    if (!row) return;

    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    row.classList.add('row--highlight');
    setTimeout(() => row.classList.remove('row--highlight'), 4500);
  })();

  // ============= MODAL: Descontar =============
  const modal = $('#modal-descontar');
  const mdSku = $('#md_sku');
  const mdQty = $('#md_qty');

  function openModalDescontar(sku = '') {
    if (!modal) return;
    if (mdSku) mdSku.value = sku || '';
    if (mdQty) mdQty.value = 1;
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.add('is-open');
    (sku ? mdQty : mdSku)?.focus();
  }
  function closeModalDescontar() {
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'true');
    modal.classList.remove('is-open');
  }

  $$('.js-open-descontar').forEach(a => {
    on(a, 'click', (e) => {
      e.preventDefault();
      openModalDescontar(a.dataset.sku || '');
    });
  });
  $$('.js-close-descontar').forEach(b => on(b, 'click', closeModalDescontar));
  on(document, 'keydown', (e) => { if (e.key === 'Escape' && modal?.classList.contains('is-open')) closeModalDescontar(); });
  on($('.modal__backdrop'), 'click', (e) => { if (e.target.dataset.close) closeModalDescontar(); });

  // =============== STEPPER +/- ===============
  function hookSteppers(root = document) {
    root.querySelectorAll('.stepper-btn').forEach(btn => {
      on(btn, 'click', () => {
        const input = btn.parentElement.querySelector('input[type="number"]');
        const step  = parseInt(btn.dataset.step || '0', 10);
        let val     = parseInt(input?.value || '1', 10);
        val = (isNaN(val) ? 1 : val + step);
        if (val < 1) val = 1;
        if (input) input.value = val;
      });
    });
  }
  hookSteppers(document);

  // ====== Fade automático de .alert (si existieran) ======
  $$('.alert').forEach(msg => {
    setTimeout(() => {
      msg.classList.add('fade-out');
      on(msg, 'transitionend', () => msg.remove(), { once: true });
    }, 5000);
  });

  // =================== ASISTENTE ===================
  const btn    = $('#assistantBtn');
  const img    = $('#assistantImg');
  const bubble = $('#assistantBubble');
  const idleSrc = btn?.dataset.idleSrc;
  const gifSrc  = btn?.dataset.gifSrc;

  let bubbleTimer = null;
  let revertTimer = null;

  function setImage(src) { if (img && src) img.src = src; }
  function say(text, delay = 0) {
    if (!btn || !bubble) return;
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {
      bubble.textContent = text;
      btn.classList.add('show-bubble');
    }, delay);
  }
  function hideBubble(delay = 0) {
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => {
      btn?.classList.remove('show-bubble');
      if (bubble) bubble.textContent = '';
    }, delay);
  }

  function playAssistant() {
    setImage(gifSrc);
    say('¡Hola! ¿Te ayudo?', 0);
    say('¡Soy tu asistente!', 1800);
  }
  function stopAssistant() {
    hideBubble(120);
    clearTimeout(revertTimer);
    revertTimer = setTimeout(() => setImage(idleSrc), 250);
  }

  if (btn) {
    on(btn, 'mouseenter', playAssistant);
    on(btn, 'focus', playAssistant);
    on(btn, 'mouseleave', stopAssistant);
    on(btn, 'blur', stopAssistant);

    on(btn, 'touchstart', (e) => { e.preventDefault(); playAssistant(); }, { passive: false });
    on(document, 'touchstart', (e) => { if (!btn.contains(e.target)) stopAssistant(); }, { passive: true });
  }
})();