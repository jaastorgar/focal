/*! FOCAL – app.js (unificado)
   Incluye:
   - Modal AJAX con actualización en vivo (upsert de filas por SKU)
   - Highlight de fila, shadow en tabla, asistente flotante
   - Bloqueo de acciones deshabilitadas
   - Checker de SKU en vivo + VALIDACIÓN ESTRICTA (solo dígitos, sin espacios)
   - Autocompletar campos si el SKU existe globalmente
*/
(function () {
  'use strict';

  // ========== Helpers ==========
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  const metaSkuTpl = document.querySelector('meta[name="sku-api-template"]');
  const skuApiTemplate = metaSkuTpl ? metaSkuTpl.getAttribute('content') : null;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
  }
  function isJsonResponse(res) {
    const ct = res.headers.get('content-type') || '';
    return ct.includes('application/json');
  }
  function toBool(v) {
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v !== 0;
    if (typeof v === 'string') {
      const t = v.trim().toLowerCase();
      return t === 'true' || t === '1' || t === 'yes' || t === 'si' || t === 'sí';
    }
    return !!v;
  }

  // ========== Highlight fila recién agregada (por ?hl= o meta highlight-sku) ==========
  (function highlightNewRow() {
    const params   = new URLSearchParams(location.search);
    const metaHL   = document.querySelector('meta[name="highlight-sku"]');
    const fromQS   = (params.get('hl') || '').trim();
    const fromMeta = metaHL ? (metaHL.getAttribute('content') || '').trim() : '';
    const skuToHL  = fromMeta || fromQS;
    if (!skuToHL) return;

    const tbody = $('#tablaInventario tbody');
    if (!tbody) return;
    const row = tbody.querySelector(`tr[data-sku="${CSS.escape(skuToHL)}"]`);
    if (!row) return;

    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    row.classList.add('row--highlight');
    setTimeout(() => row.classList.remove('row--highlight'), 4500);
  })();

  // ========== Sombra de encabezado cuando la tabla scrollea ==========
  (function shadowOnScroll(){
    const tc = document.querySelector('.table-container');
    if (!tc) return;
    const update = () => tc.classList.toggle('has-scroll', tc.scrollTop > 0);
    on(tc, 'scroll', update);
    update();
  })();

  // ========== Asistente flotante ==========
  (function assistant(){
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

  // ========== Bloqueo seguro de acciones deshabilitadas ==========
  (function blockDisabled(){
    $$('.is-disabled, a[aria-disabled="true"]').forEach(a => {
      on(a, 'click', (e) => {
        e.preventDefault(); e.stopPropagation();
        const title = a.getAttribute('title') || 'Acción no disponible';
        a.setAttribute('aria-label', title);
      });
    });
    on(document, 'click', (e) => {
      const target = e.target.closest('button, input[type="submit"]');
      if (!target) return;
      if (target.hasAttribute('disabled') || target.getAttribute('aria-disabled') === 'true') {
        e.preventDefault(); e.stopPropagation();
      }
    });
  })();

  // ========== MODAL AJAX (unificado) ==========
  const overlay   = $('[data-modal-overlay]');
  const modalBody = $('#modal-body');
  const modalTit  = $('#modal-title');
  const tableBody = $('#tablaInventario tbody');

  if (!overlay || !modalBody || !modalTit) {
    console.warn('[app.js] Falta estructura del modal en el DOM.');
    return;
  }

  let lastTrigger = null;
  let focusablesCache = [];
  let previousActive = null;

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

  function openModal(triggerNode) {
    previousActive = document.activeElement;
    lastTrigger = triggerNode || null;
    overlay.hidden = false;
    document.addEventListener('keydown', onKeyDown, true);
    overlay.addEventListener('keydown', trapFocus, true);
    lockBodyScroll();

    setTimeout(() => {
      focusablesCache = getFocusables(overlay);
      const firstField = modalBody.querySelector('input, select, textarea, [autofocus]');
      if (firstField) firstField.focus();
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
          const res = await fetch(href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          if (isJsonResponse(res)) {
            const json = await res.json();
            modalBody.innerHTML = json.html || '<p>Sin contenido.</p>';
          } else {
            modalBody.innerHTML = await res.text();
          }
          wireForm();               // enlaza envío del form
          bindModalLinks(modalBody);// por si hay enlaces internos que abren modales
          openModal(el);
        } catch (err) {
          console.error('[app.js] Error al cargar modal:', err);
          modalBody.innerHTML = '<p>Ocurrió un problema al cargar el contenido.</p>';
          openModal(el);
        }
      });
    });
  }

  function upsertRowBySku(sku, rowHtml) {
    if (!tableBody || !rowHtml) return false;
    const temp = document.createElement('tbody');
    temp.innerHTML = rowHtml.trim();
    const newRow = temp.querySelector('tr');
    if (!newRow) return false;

    const existing = tableBody.querySelector(`tr[data-sku="${CSS.escape(sku)}"]`);
    if (existing) { existing.replaceWith(newRow); pulseRow(newRow); return 'updated'; }
    tableBody.prepend(newRow); pulseRow(newRow); return 'inserted';
  }
  function pulseRow(row) {
    row.style.transition = 'background-color .8s ease';
    const original = row.style.backgroundColor;
    row.style.backgroundColor = 'rgba(108, 0, 180, .12)';
    setTimeout(() => { row.style.backgroundColor = original || ''; }, 800);
  }
  function showToast(text) {
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

  // ========= Checker de SKU en vivo (con validación estricta + autocompletar) =========
  function attachSkuChecker(formRoot) {
    if (!skuApiTemplate) return; // no hay endpoint configurado
    const skuField = formRoot.querySelector('input[name="sku"]');
    if (!skuField) return;

    // Atributos de ayuda al navegador/móvil
    skuField.setAttribute('inputmode', 'numeric');
    skuField.setAttribute('pattern', '\\d*');
    skuField.setAttribute('autocomplete', 'off');

    // Crea (o reutiliza) un nodo de estado junto al campo
    let statusNode = formRoot.querySelector('.sku-status-hint');
    if (!statusNode) {
      statusNode = document.createElement('div');
      statusNode.className = 'sku-status-hint';
      statusNode.style.fontSize = '12px';
      statusNode.style.marginTop = '6px';
      statusNode.style.fontWeight = '600';
      statusNode.style.lineHeight = '1.25';
      const wrap = skuField.closest('.form-field') || skuField.parentElement;
      wrap && wrap.appendChild(statusNode);
    }

    let debTimer = null;
    function setHint(text, color) {
      statusNode.textContent = text || '';
      statusNode.style.color = color || '#555';
    }

    // --- Validación en tiempo real: solo dígitos ---
    function sanitizeValue(raw) {
      return (raw || '').replace(/\D+/g, ''); // elimina todo lo que no sea 0-9
    }

    function sanitizeOnInput(e) {
      const oldVal = e.target.value;
      const newVal = sanitizeValue(oldVal);
      if (newVal !== oldVal) {
        const start = e.target.selectionStart || newVal.length;
        e.target.value = newVal;
        try { e.target.setSelectionRange(start - 1, start - 1); } catch(_) {}
      }
    }

    function preventNonDigits(e) {
      const ctrlKeys = ['Backspace','Delete','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','Tab','Enter'];
      if (ctrlKeys.includes(e.key)) return;
      if (e.ctrlKey || e.metaKey) return;
      if (!/^\d$/.test(e.key)) e.preventDefault();
    }

    function onPaste(e) {
      const text = (e.clipboardData || window.clipboardData).getData('text');
      const clean = sanitizeValue(text);
      if (text !== clean) {
        e.preventDefault();
        document.execCommand('insertText', false, clean);
      }
    }

    // Bind de validación estricta
    skuField.removeEventListener('keydown', skuField.__skuKeydown || (()=>{}));
    skuField.removeEventListener('paste',   skuField.__skuPaste   || (()=>{}));
    skuField.removeEventListener('input',   skuField.__skuSanIn   || (()=>{}));

    skuField.__skuKeydown = preventNonDigits;
    skuField.__skuPaste   = onPaste;
    skuField.__skuSanIn   = sanitizeOnInput;

    skuField.addEventListener('keydown', preventNonDigits);
    skuField.addEventListener('paste', onPaste);
    skuField.addEventListener('input', sanitizeOnInput);

    // --- Autocompletar campos si la API los expone ---
    function applyAutocomplete(payload, form) {
      const d = payload?.datos || payload?.product || payload || {};
      const map = {
        nombre: 'id_nombre',
        marca: 'id_marca',
        categoria: 'id_categoria',
        gramaje: 'id_gramaje',
        unidad_medida: 'id_unidad_medida',
      };
      // Solo autocompleta si el campo está vacío para no pisar lo que escribió el usuario
      if (d.nombre && form.querySelector('#' + map.nombre)?.value === '') form.querySelector('#' + map.nombre).value = d.nombre;
      if (d.marca && form.querySelector('#' + map.marca)?.value === '') form.querySelector('#' + map.marca).value = d.marca;
      if (d.categoria && form.querySelector('#' + map.categoria)) form.querySelector('#' + map.categoria).value = d.categoria;
      if (d.gramaje && form.querySelector('#' + map.gramaje)?.value === '') form.querySelector('#' + map.gramaje).value = d.gramaje;
      if (d.unidad_medida && form.querySelector('#' + map.unidad_medida)) form.querySelector('#' + map.unidad_medida).value = d.unidad_medida;
    }

    // --- Consulta a API para disponibilidad/existencia ---
    async function checkSku(value) {
      const sku = (value || '').trim();
      if (!sku) { setHint('', null); return; }
      const url = skuApiTemplate.replace('SKU_PLACEHOLDER', encodeURIComponent(sku));
      try {
        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' });
        if (!res.ok) { 
          // Si la API devuelve 404 u otro error, lo tratamos como "no encontrado globalmente"
          setHint('Disponible ✅', '#0a7f30'); 
          return; 
        }
        const data = await res.json();

        // Campos posibles (normalizados)
        const inCompany = toBool(
          data.in_company ?? data.in_inventory ?? data.existe_en_empresa ?? data.ya_en_inventario ?? data.pertenece_empresa
        );
        const exists = toBool(
          data.exists ?? data.existe_global ?? data.existe ?? data.found ?? data.en_catalogo ?? data.in_catalog
        );

        // También soporta payloads tipo {status: "in_company"|"exists"|"available"}
        const status = (data.status || data.estado || '').toString().toLowerCase();
        const byStatus_inCompany = status === 'in_company' || status === 'en_empresa' || status === 'inventario' || status === 'duplicado_local';
        const byStatus_exists    = status === 'exists' || status === 'catalogo' || status === 'catalog' || status === 'encontrado_global';

        const finalInCompany = inCompany || byStatus_inCompany;
        const finalExists    = exists || byStatus_exists;

        if (finalInCompany) {
          setHint('Ya está en tu inventario ⚠️', '#b00020');
          return;
        }
        if (finalExists) {
          // autocompletar si existe globalmente
          applyAutocomplete(data, formRoot);
          setHint('Existe en catálogo (se asociará) ℹ️', '#8a6700');
          return;
        }
        setHint('Disponible ✅', '#0a7f30');
      } catch (e) {
        // Ante error de red u otro, no bloquear: dejarlo como “disponible (no verificado)”
        setHint('Disponible (no verificado) ⚠️', '#8a6700');
      }
    }

    const debouncedCheck = () => {
      clearTimeout(debTimer);
      debTimer = setTimeout(() => checkSku(skuField.value), 250);
    };

    skuField.removeEventListener('keyup', skuField.__skuDeb || (()=>{}));
    skuField.__skuDeb = debouncedCheck;
    skuField.addEventListener('keyup', debouncedCheck);

    // Ejecutar verificación inicial al abrir modal
    debouncedCheck();
  }

  // ========== Envío de formulario dentro del modal ==========
  function wireForm() {
    const form = $('#modal-dynamic-form', modalBody);
    if (!form) return;

    // Engancha checker + validación SKU
    attachSkuChecker(form);

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
            if (json.redirect) { window.location.href = json.redirect; return; }
            if (json.row_html && json.sku) {
              const result = upsertRowBySku(json.sku, json.row_html);
              closeModal();
              if (result === 'inserted') showToast('Producto agregado al inventario');
              else if (result === 'updated') showToast('Producto actualizado');
              else showToast('Cambios aplicados');
              return;
            }
            closeModal();
            window.location.reload();
            return;
          }

          if (json.html) {
            modalBody.innerHTML = json.html;
            wireForm();
            bindModalLinks(modalBody);
            focusFirstError();
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
        focusFirstError();

      } catch (err) {
        console.error('[app.js] Error al enviar formulario:', err);
        alert('No pudimos completar la acción. Intenta nuevamente.');
      }
    });
  }

  function focusFirstError() {
    const firstErr = $('.error, [aria-invalid="true"]', modalBody) || $('input, select, textarea', modalBody);
    if (firstErr && typeof firstErr.focus === 'function') firstErr.focus();
  }

  // ========== Init ==========
  function init() {
    bindModalLinks();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  // API mínima opcional
  window.FocalApp = {
    openModal(html, title='Acción'){ modalTit.textContent = title; modalBody.innerHTML = html; openModal(); },
    closeModal,
    refreshBindings: bindModalLinks,
    upsertRowBySku
  };

})();