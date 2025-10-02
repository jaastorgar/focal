/*! FOCAL - inventario_app.js (único)
   Tabs + modal descontar + stepper + fade alerts
   + Asistente (GIF + globito de ayuda)
*/
(function () {
  'use strict';

  // ---------- Helpers ----------
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => r.querySelectorAll(s);
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  /* ================== TABS ================== */
  const tabs = $$('.tab-btn');
  const panels = $$('.tab-panel');

  function setActive(id) {
    if (!id) return;
    tabs.forEach(b => b.classList.toggle('active', b.dataset.tab === id));
    panels.forEach(p => p.classList.toggle('active', p.id === id));
    if (location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
    if (id === 'tab-descontar') { $('#id_sku_desc')?.focus(); }
    if (id === 'tab-gestionar') { $('#id_sku')?.focus(); }
  }

  tabs.forEach(btn => on(btn, 'click', () => setActive(btn.dataset.tab)));
  if (location.hash && $(location.hash)) setActive(location.hash.substring(1));
  else setActive('tab-inv');

  const params = new URLSearchParams(location.search);
  if (params.get('sku')) setActive('tab-gestionar');

  /* ============ MODAL: Descontar ============ */
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
  on(document, 'keydown', (e) => {
    if (e.key === 'Escape' && modal?.classList.contains('is-open')) closeModalDescontar();
  });
  on($('.modal__backdrop'), 'click', (e) => { if (e.target.dataset.close) closeModalDescontar(); });

  /* =============== STEPPER +/- =============== */
  function hookSteppers(root = document) {
    root.querySelectorAll('.stepper-btn').forEach(btn => {
      on(btn, 'click', () => {
        const input = btn.parentElement.querySelector('input[type="number"]');
        const step = parseInt(btn.dataset.step || '0', 10);
        let val = parseInt(input?.value || '1', 10);
        val = (isNaN(val) ? 1 : val + step);
        if (val < 1) val = 1;
        if (input) input.value = val;
      });
    });
  }
  hookSteppers(document);

  /* ====== Fade automático de .alert (si las hubiese) ====== */
  on(document, 'DOMContentLoaded', () => {
    $$('.alert').forEach(msg => {
      setTimeout(() => {
        msg.classList.add('fade-out');
        on(msg, 'transitionend', () => msg.remove(), { once: true });
      }, 5000);
    });
  });

  /* =================== ASISTENTE =================== */
  const btn = $('#assistantBtn');
  const img = $('#assistantImg');
  const bubble = $('#assistantBubble');
  const idleSrc = btn?.dataset.idleSrc;
  const gifSrc = btn?.dataset.gifSrc;

  let bubbleTimer = null;
  let revertTimer = null;

  function setImage(src) {
    if (img && src) img.src = src;  // cambiar PNG <-> GIF
  }

  // Muestra mensaje en el globito
  function say(text, delay = 0) {
    if (!btn || !bubble) return;
    window.clearTimeout(bubbleTimer);
    bubbleTimer = window.setTimeout(() => {
      bubble.textContent = text;
      btn.classList.add('show-bubble');
    }, delay);
  }

  function hideBubble(delay = 0) {
    window.clearTimeout(bubbleTimer);
    bubbleTimer = window.setTimeout(() => {
      btn?.classList.remove('show-bubble');
      if (bubble) bubble.textContent = '';
    }, delay);
  }

  // Al entrar (hover/focus/touch) -> reproducir GIF + frases
  function playAssistant() {
    setImage(gifSrc);
    say('¡Hola! ¿Te ayudo?', 0);
    say('¡Soy tu asistente!', 1800);
  }

  // Al salir -> volver a PNG y ocultar burbuja
  function stopAssistant() {
    hideBubble(120);
    window.clearTimeout(revertTimer);
    revertTimer = window.setTimeout(() => setImage(idleSrc), 250);
  }

  if (btn) {
    // Mouse/keyboard
    on(btn, 'mouseenter', playAssistant);
    on(btn, 'focus', playAssistant);
    on(btn, 'mouseleave', stopAssistant);
    on(btn, 'blur', stopAssistant);

    // Touch (móviles): tocar -> anima y muestra; tocar fuera -> oculta
    on(btn, 'touchstart', (e) => {
      e.preventDefault();
      playAssistant();
    }, { passive: false });

    on(document, 'touchstart', (e) => {
      if (!btn.contains(e.target)) stopAssistant();
    }, { passive: true });

    // Click (si quieres abrir algo futuro)
    on(btn, 'click', () => {
      // Aquí podrías abrir tu panel/chat real del asistente
      // Por ahora solo dejamos la animación.
    });
  }
})();