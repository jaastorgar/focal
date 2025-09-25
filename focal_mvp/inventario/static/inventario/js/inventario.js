/*! FOCAL - inventario_app.js (único)
   Unifica: tabs + gestionar/descontar/agregar + modal de descontar + stepper + fade alerts
   Reemplaza a: inventario/js/inventario.js y inventario/js/hub.js
*/
(function(){
  'use strict';

  // ---------- Helpers ----------
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => r.querySelectorAll(s);
  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  // ---------- Tabs ----------
  const tabs = $$('.tab-btn');
  const panels = $$('.tab-panel');

  function setActive(id){
    if(!id) return;
    tabs.forEach(b=>b.classList.toggle('active', b.dataset.tab===id));
    panels.forEach(p=>p.classList.toggle('active', p.id===id));
    // sync hash
    if(location.hash !== '#'+id) history.replaceState(null,'','#'+id);
    // UX focus
    if(id==='tab-descontar'){ $('#id_sku_desc')?.focus(); }
    if(id==='tab-gestionar'){ $('#id_sku')?.focus(); }
  }

  tabs.forEach(btn=> on(btn,'click', ()=> setActive(btn.dataset.tab)));

  if(location.hash && $(location.hash)){
    setActive(location.hash.substring(1));
  }else{
    setActive('tab-inv');
  }

  const params = new URLSearchParams(location.search);
  if(params.get('sku')) setActive('tab-gestionar');

  // ---------- Acciones desde la tabla -> abrir MODAL de Descontar ----------
  const modal = $('#modal-descontar');
  const mdSku = $('#md_sku');
  const mdQty = $('#md_qty');

  function openModalDescontar(sku=''){
    if(!modal) return;
    mdSku && (mdSku.value = sku || '');
    mdQty && (mdQty.value = 1);
    modal.setAttribute('aria-hidden','false');
    modal.classList.add('is-open');
    // foco al SKU si viene vacío, sino a la cantidad
    (sku ? mdQty : mdSku)?.focus();
  }
  function closeModalDescontar(){
    if(!modal) return;
    modal.setAttribute('aria-hidden','true');
    modal.classList.remove('is-open');
  }

  $$('.js-open-descontar').forEach(a=>{
    on(a, 'click', (e)=>{
      e.preventDefault();
      openModalDescontar(a.dataset.sku || '');
    });
  });
  $$('.js-close-descontar').forEach(b=> on(b,'click', closeModalDescontar));

  on(document, 'keydown', (e)=>{
    if(e.key === 'Escape' && modal?.classList.contains('is-open')) closeModalDescontar();
  });
  // cerrar si se hace click en backdrop
  on($('.modal__backdrop'), 'click', (e)=>{ if(e.target.dataset.close) closeModalDescontar(); });

  // ---------- Stepper +/− (tab y modal) ----------
  function hookSteppers(root=document){
    root.querySelectorAll('.stepper-btn').forEach(btn=>{
      on(btn, 'click', ()=>{
        const input = btn.parentElement.querySelector('input[type="number"]');
        const step = parseInt(btn.dataset.step || '0', 10);
        let val = parseInt(input?.value || '1', 10);
        val = (isNaN(val) ? 1 : val + step);
        if(val < 1) val = 1;
        if(input) input.value = val;
      });
    });
  }
  hookSteppers(document);

  // ---------- Autocompletar por SKU (pestaña Agregar) ----------
  function getSkuApiTemplate(){
    return $('#form-agregar-prod')?.dataset?.skuApiTpl
        || $('meta[name="sku-api-template"]')?.getAttribute('content')
        || (typeof window!=='undefined' && window.SKU_API_TEMPLATE)
        || '';
  }

  async function consultarSkuYAutocompletar(){
    const sku = ($('#id_sku_add')?.value || '').trim();
    const msg = $('#sku_add_msg') || { textContent: null };
    if(!sku){ msg.textContent='Ingresa un SKU'; return; }

    const tpl = getSkuApiTemplate();
    if(!tpl){ msg.textContent='No se definió el endpoint de consulta de SKU.'; return; }

    msg.textContent='Consultando...';
    try{
      const api = tpl.replace('SKU_PLACEHOLDER', encodeURIComponent(sku));
      const resp = await fetch(api, { headers: { 'Accept': 'application/json' }});
      if(!resp.ok) throw new Error('HTTP '+resp.status);
      const data = await resp.json();

      if(data.status==='duplicado_local'){
        msg.textContent='Este producto ya existe en tu inventario.';
      }else if(data.status==='encontrado_global'){
        msg.textContent='Encontrado en catálogo global. Campos autocompletados.';
        $('#f_sku') && ($('#f_sku').value = data.datos.sku || sku);
        $('#f_nombre') && ($('#f_nombre').value = data.datos.nombre || '');
        $('#f_marca') && ($('#f_marca').value = data.datos.marca || '');
        $('#f_categoria') && ($('#f_categoria').value = data.datos.categoria || '');
        $('#f_dramage') && ($('#f_dramage').value = data.datos.dramage || '');
        $('#f_unidad') && ($('#f_unidad').value = data.datos.unidad_medida || '');
      }else{
        msg.textContent='SKU no encontrado. Completa el formulario para crearlo.';
        $('#f_sku') && ($('#f_sku').value = sku);
      }
    }catch(err){
      msg.textContent='Error consultando el SKU.';
      console.error('[SKU API] Error:', err);
    }
  }

  on($('#btn_buscar_sku_add'), 'click', consultarSkuYAutocompletar);
  on($('#id_sku_add'), 'keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); consultarSkuYAutocompletar(); } });

  // ---------- Fade automático de mensajes .alert ----------
  on(document, 'DOMContentLoaded', ()=>{
    $$('.alert').forEach(msg=>{
      setTimeout(()=>{
        msg.classList.add('fade-out');
        on(msg, 'transitionend', ()=> msg.remove(), { once:true });
      }, 5000);
    });
  });

})();