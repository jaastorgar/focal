(function(){
  const $ = (sel)=>document.querySelector(sel);
  const priceEl = $('#preview');
  const calcLine = $('#calcLine');
  const amountEl = $('#amount_clp');
  const skuEl = $('#sku');
  const btnPreview = $('#btnPreviewSKU');

  function numberFormat(x){
    try{
      return new Intl.NumberFormat('es-CL').format(x);
    }catch(e){ return x; }
  }

  function roundToStep(grams, step){
    if(step <= 1) return grams;
    const remainder = grams % step;
    if(remainder === 0) return grams;
    const down = grams - remainder;
    const up = down + step;
    return ((grams - down) >= (step/2)) ? up : down;
  }

  function recalc(){
    const precio = parseFloat(priceEl.dataset.precioKg || '0');
    const step = parseInt(priceEl.dataset.minStep || '5', 10);
    const amount = parseInt(amountEl.value || '0', 10);

    if(!precio || precio <= 0){
      calcLine.innerHTML = 'Define un SKU válido para conocer el precio por kg.';
      return;
    }
    if(!amount || amount <= 0){
      calcLine.innerHTML = 'Escribe un monto para calcular los gramos sugeridos.';
      return;
    }

    const gramsRaw = Math.round((amount / precio) * 1000);
    const gramsFinal = roundToStep(gramsRaw, step);
    calcLine.innerHTML = `
      <div>Conversión: $${numberFormat(amount)} → <b class="ok">${numberFormat(gramsFinal)} g</b></div>
      <div class="muted">Cálculo base: (monto / precio_kg) * 1000 = ${numberFormat(gramsRaw)} g → redondeo ${step} g</div>
    `;
  }

  amountEl && amountEl.addEventListener('input', recalc);

  btnPreview && btnPreview.addEventListener('click', function(){
    const sku = (skuEl.value || '').trim();
    if(!sku){ alert('Ingresa un SKU para previsualizar.'); return; }
    const url = new URL(window.location.href);
    url.searchParams.set('sku', sku);
    window.location.href = url.toString();
  });

  // Recalcular si la página ya trae precio (SKU previsualizado)
  if(parseFloat(priceEl.dataset.precioKg || '0') > 0){
    recalc();
  }
})();