/* =========================================================
   MODAL AJAX FOCAL – static/inventario/js/modal.js
   Ahora con actualización en vivo de la tabla (sin reload):
   - Usa json.row_html + json.sku (+ json.action opcional)
   ========================================================= */

(function () {
  // ---------- Utils ----------
  const qs  = (s, p = document) => p.querySelector(s);
  const qsa = (s, p = document) => Array.from(p.querySelectorAll(s));

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
  }

  function isJsonResponse(res) {
    const ct = res.headers.get('content-type') || '';
    return ct.includes('application/json');
  }

  function lockBodyScroll() {
    const scrollBarComp = window.innerWidth - document.documentElement.clientWidth;
    document.body.dataset.prevOverflow = document.body.style.overflow || '';
    document.body.style.overflow = 'hidden';
    if (scrollBarComp > 0) document.body.style.paddingRight = `${scrollBarComp}px`;
  }

  function unlockBodyScroll() {
    document.body.style.overflow = document.body.dataset.prevOverflow || '';
    document.body.style.paddingRight = '';
    delete document.body.dataset.prevOverflow;
  }

  // ---------- Elementos base ----------
  const overlay = qs('[data-modal-overlay]');
  const bodyEl  = qs('#modal-body');
  const titleEl = qs('#modal-title');
  const tableBody = qs('#tablaInventario tbody');

  if (!overlay || !bodyEl || !titleEl) {
    console.warn('[modal.js] Faltan nodos del modal en el DOM.');
    return;
  }

  let lastTrigger = null;
  let focusablesCache = [];
  let previousActive = null;

  // ---------- Apertura / Cierre ----------
  function openModal(triggerNode) {
    previousActive = document.activeElement;
    lastTrigger = triggerNode || null;
    overlay.hidden = false;
    document.addEventListener('keydown', onKeyDown, true);
    overlay.addEventListener('keydown', trapFocus, true);
    lockBodyScroll();

    setTimeout(() => {
      focusablesCache = getFocusables(overlay);
      const firstField = qs('input, select, textarea, [autofocus]', bodyEl);
      if (firstField) firstField.focus();
      else if (focusablesCache[0]) focusablesCache[0].focus();
      else qs('[data-modal-close]', overlay)?.focus();
    }, 0);
  }

  function closeModal() {
    overlay.hidden = true;
    bodyEl.innerHTML = '';
    document.removeEventListener('keydown', onKeyDown, true);
    overlay.removeEventListener('keydown', trapFocus, true);
    unlockBodyScroll();
    if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus();
    else if (previousActive && document.contains(previousActive)) previousActive.focus();
    lastTrigger = null;
    previousActive = null;
    focusablesCache = [];
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') { e.preventDefault(); closeModal(); }
  }

  // ---------- Trap Focus ----------
  function getFocusables(root) {
    const selectors = [
      'a[href]','button:not([disabled])','textarea:not([disabled])',
      'input:not([disabled])','select:not([disabled])','[tabindex]:not([tabindex="-1"])'
    ].join(',');
    return qsa(selectors, root).filter(el => el.offsetParent !== null || el === document.activeElement);
  }
  function trapFocus(e) {
    if (e.key !== 'Tab') return;
    const focusables = focusablesCache.length ? focusablesCache : getFocusables(overlay);
    if (!focusables.length) return;
    const first = focusables[0], last = focusables[focusables.length - 1];
    if (e.shiftKey) { if (document.activeElement === first || document.activeElement === overlay) { e.preventDefault(); last.focus(); } }
    else { if (document.activeElement === last) { e.preventDefault(); first.focus(); } }
  }

  // ---------- Eventos de cierre ----------
  overlay.addEventListener('click', (e) => {
    if (e.target.hasAttribute('data-modal-overlay') || e.target.hasAttribute('data-modal-close')) closeModal();
  });

  // ---------- Enlaces que abren modal ----------
  function bindModalLinks(ctx = document) {
    qsa('[data-modal="ajax"]', ctx).forEach(el => {
      if (el.__boundModal) return;
      el.__boundModal = true;
      el.addEventListener('click', async (e) => {
        const isLink = el.tagName === 'A';
        const href = isLink ? el.getAttribute('href') : (el.dataset.href || el.getAttribute('data-href'));
        if (!href) return;
        e.preventDefault();
        const title = el.getAttribute('data-modal-title') || el.getAttribute('title') || 'Acción';
        titleEl.textContent = title;

        try {
          const res = await fetch(href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          if (isJsonResponse(res)) {
            const json = await res.json();
            bodyEl.innerHTML = json.html || '<p>Sin contenido.</p>';
          } else {
            const html = await res.text();
            bodyEl.innerHTML = html;
          }
          wireForm();
          bindModalLinks(bodyEl);
          openModal(el);
        } catch (err) {
          console.error('[modal.js] Error al cargar modal:', err);
          bodyEl.innerHTML = '<p>Ocurrió un problema al cargar el contenido.</p>';
          openModal(el);
        }
      });
    });
  }

  // ---------- Inserción/actualización en vivo de filas ----------
  function upsertRowBySku(sku, rowHtml) {
    if (!tableBody || !rowHtml) return false;
    const temp = document.createElement('tbody');
    temp.innerHTML = rowHtml.trim();
    const newRow = temp.querySelector('tr');
    if (!newRow) return false;

    let existing = tableBody.querySelector(`tr[data-sku="${CSS.escape(sku)}"]`);
    if (existing) {
      existing.replaceWith(newRow);
      pulseRow(newRow);
      return 'updated';
    } else {
      // Si no existe, insertar al principio (puedes cambiar a append)
      tableBody.prepend(newRow);
      pulseRow(newRow);
      return 'inserted';
    }
  }

  function pulseRow(row) {
    row.style.transition = 'background-color .8s ease';
    const original = row.style.backgroundColor;
    row.style.backgroundColor = 'rgba(108, 0, 180, .12)'; // highlight
    setTimeout(() => { row.style.backgroundColor = original || ''; }, 800);
  }

  function showToast(text) {
    // Reutiliza tu stack de toasts si existe; fallback simple:
    const holder = document.createElement('div');
    holder.setAttribute('role','status');
    holder.style.position = 'fixed';
    holder.style.right = '16px';
    holder.style.bottom = '16px';
    holder.style.zIndex = '10000';
    holder.innerHTML = `<div style="background:#6A0DAD;color:#fff;padding:10px 14px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.2);font-weight:600;">${text}</div>`;
    document.body.appendChild(holder);
    setTimeout(() => holder.remove(), 2200);
  }

  // ---------- Envío del formulario dentro del modal ----------
  function wireForm() {
    const form = qs('#modal-dynamic-form', bodyEl);
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
        const res = await fetch(action, { method, headers, body: data });

        if (isJsonResponse(res)) {
          const json = await res.json();

          if (json.ok) {
            // 1) Si hay redirect explícito, respetarlo
            if (json.redirect) { window.location.href = json.redirect; return; }

            // 2) Si viene row_html + sku, actualizamos tabla sin recargar
            if (json.row_html && json.sku) {
              const result = upsertRowBySku(json.sku, json.row_html);
              closeModal();
              if (result === 'inserted') showToast('Producto agregado al inventario');
              else if (result === 'updated') showToast('Producto actualizado');
              else showToast('Cambios aplicados');
              return;
            }

            // 3) Fallback: cerrar y recargar
            closeModal();
            window.location.reload();
            return;
          }

          // Errores de validación con html del form
          if (json.html) {
            bodyEl.innerHTML = json.html;
            wireForm();
            bindModalLinks(bodyEl);
            focusFirstError();
            return;
          }

          // Error genérico
          bodyEl.innerHTML = '<p>Ocurrió un error al guardar.</p>';
          return;
        }

        // Si vino HTML (form con errores)
        const html = await res.text();
        bodyEl.innerHTML = html;
        wireForm();
        bindModalLinks(bodyEl);
        focusFirstError();

      } catch (err) {
        console.error('[modal.js] Error al enviar formulario:', err);
        alert('No pudimos completar la acción. Intenta nuevamente.');
      }
    });
  }

  function focusFirstError() {
    const firstErr = qs('.error, [aria-invalid="true"]', bodyEl) || qs('input, select, textarea', bodyEl);
    if (firstErr && typeof firstErr.focus === 'function') firstErr.focus();
  }

  // ---------- Inicialización ----------
  function init() {
    bindModalLinks();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  // API mínima
  window.FocalModal = {
    open: (html, title = 'Acción') => { titleEl.textContent = title; bodyEl.innerHTML = html; openModal(); },
    close: closeModal,
    refreshBindings: bindModalLinks,
    upsertRowBySku
  };
})();