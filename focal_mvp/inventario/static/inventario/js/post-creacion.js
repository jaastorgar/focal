/*! FOCAL – post-creacion.js
   Núcleo de modal independiente para la página Post-Creación.
   - Abre enlaces con data-modal="ajax" en una ventana emergente
   - Carga el <form> vía AJAX (GET)
   - Envía el <form> vía AJAX (POST)
   - Soporta respuestas JSON {ok, html?, redirect?, row_html?, sku?} o HTML con errores
*/

(function () {
  'use strict';

  // ===== Helpers =====
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  function isJsonResponse(res) {
    const ct = res.headers.get('content-type') || '';
    return ct.includes('application/json');
  }
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
  }

  // ===== Referencias del modal (deben existir en el DOM) =====
  const overlay   = $('[data-modal-overlay]');
  const modalBody = $('#modal-body');
  const modalTit  = $('#modal-title');

  if (!overlay || !modalBody || !modalTit) {
    console.warn('[post-creacion.js] Falta estructura del modal en el DOM.');
    return;
  }

  let lastTrigger = null;
  let focusablesCache = [];
  let previousActive = null;

  // ===== Apertura / cierre / accesibilidad =====
  function lockBodyScroll() {
    const comp = window.innerWidth - document.documentElement.clientWidth;
    document.body.dataset.prevOverflow = document.body.style.overflow || '';
    document.body.style.overflow = 'hidden';
    if (comp > 0) document.body.style.paddingRight = `${comp}px`;
  }
  function unlockBodyScroll() {
    document.body.style.overflow = document.body.dataset.prevOverflow || '';
    document.body.style.paddingRight = '';
    delete document.body.dataset.prevOverflow;
  }

  function openModal(triggerNode) {
    previousActive = document.activeElement;
    lastTrigger = triggerNode || null;
    overlay.hidden = false;
    document.addEventListener('keydown', onKeyDown, true);
    overlay.addEventListener('keydown', trapFocus, true);
    lockBodyScroll();

    setTimeout(() => {
      focusablesCache = getFocusables(overlay);
      const first = modalBody.querySelector('input, select, textarea, [autofocus]');
      if (first) first.focus();
      else if (focusablesCache[0]) focusablesCache[0].focus();
      else $('[data-modal-close]', overlay)?.focus();
    }, 0);
  }

  function closeModal() {
    overlay.hidden = true;
    modalBody.innerHTML = '';
    document.removeEventListener('keydown', onKeyDown, true);
    overlay.removeEventListener('keydown', trapFocus, true);
    unlockBodyScroll();
    if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus();
    else if (previousActive && document.contains(previousActive)) previousActive.focus();
    lastTrigger = null; previousActive = null; focusablesCache = [];
  }

  function onKeyDown(e) { if (e.key === 'Escape') { e.preventDefault(); closeModal(); } }

  function getFocusables(root) {
    const selectors = [
      'a[href]','button:not([disabled])','textarea:not([disabled])',
      'input:not([disabled])','select:not([disabled])','[tabindex]:not([tabindex="-1"])'
    ].join(',');
    return $$(selectors, root).filter(el => el.offsetParent !== null || el === document.activeElement);
  }
  function trapFocus(e) {
    if (e.key !== 'Tab') return;
    const f = focusablesCache.length ? focusablesCache : getFocusables(overlay);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey) { if (document.activeElement === first || document.activeElement === overlay) { e.preventDefault(); last.focus(); } }
    else { if (document.activeElement === last) { e.preventDefault(); first.focus(); } }
  }

  overlay.addEventListener('click', (e) => {
    if (e.target.hasAttribute('data-modal-overlay') || e.target.hasAttribute('data-modal-close')) closeModal();
  });

  // ===== Vincular enlaces que abren el modal =====
  function bindModalLinks(ctx = document) {
    $$('[data-modal="ajax"]', ctx).forEach(el => {
      if (el.__boundModal) return;
      el.__boundModal = true;

      el.addEventListener('click', async (e) => {
        const isLink = el.tagName === 'A';
        const href = isLink ? el.getAttribute('href') : (el.dataset.href || el.getAttribute('data-href'));
        if (!href) return;
        e.preventDefault();

        const title = el.getAttribute('data-modal-title') || el.getAttribute('title') || 'Acción';
        modalTit.textContent = title;

        try {
          const res = await fetch(href, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);

          if (isJsonResponse(res)) {
            const json = await res.json();
            modalBody.innerHTML = json.html || '<p>Sin contenido.</p>';
          } else {
            modalBody.innerHTML = await res.text();
          }
          wireForm();               // engancha el envío del form
          bindModalLinks(modalBody);// por si dentro del modal hay más enlaces modal
          openModal(el);
        } catch (err) {
          console.error('[post-creacion.js] Error al cargar modal:', err);
          modalBody.innerHTML = '<p>Ocurrió un problema al cargar el contenido.</p>';
          openModal(el);
        }
      });
    });
  }

  // ===== Envío de formulario dentro del modal =====
  function wireForm() {
    const form = $('#modal-dynamic-form', modalBody);
    if (!form) return;

    const action = form.getAttribute('action') || window.location.href;
    const method = (form.getAttribute('method') || 'post').toUpperCase();

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const data = new FormData(form);
      const headers = { 'X-Requested-With': 'XMLHttpRequest' };
      if (method !== 'GET') {
        const csrfFromCookie = getCookie('csrftoken');
        const csrfFromInput  = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        headers['X-CSRFToken'] = csrfFromCookie || csrfFromInput || '';
      }

      try {
        const res = await fetch(action, { method, headers, body: data, credentials: 'same-origin' });

        if (isJsonResponse(res)) {
          const json = await res.json();

          if (json.ok) {
            // Si la vista retorna redirect, lo seguimos
            if (json.redirect) { window.location.href = json.redirect; return; }

            // Si retorna HTML de fila (no es el caso típico en post-creación), cerramos modal
            if (json.row_html && json.sku) {
              closeModal();
              window.location.reload(); // o podrías actualizar una lista si existiera
              return;
            }

            closeModal();
            window.location.reload();
            return;
          }

          // Si trae el form con errores
          if (json.html) {
            modalBody.innerHTML = json.html;
            wireForm();
            bindModalLinks(modalBody);
            return;
          }

          modalBody.innerHTML = '<p>Ocurrió un error al guardar.</p>';
          return;
        }

        // HTML con errores
        const html = await res.text();
        modalBody.innerHTML = html;
        wireForm();
        bindModalLinks(modalBody);

      } catch (err) {
        console.error('[post-creacion.js] Error al enviar formulario:', err);
        alert('No pudimos completar la acción. Intenta nuevamente.');
      }
    });
  }

  // ===== Init =====
  function init() { bindModalLinks(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

})();