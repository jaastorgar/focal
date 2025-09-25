/* Métricas – inicialización de gráficos y pequeños helpers */

(function () {
  const CH = window.FOCAL_CHARTS || {};

  // Helper: si no hay datos, oculta canvas y muestra mensaje
  function showEmptyIfNeeded(canvasId, emptyId, labels, values) {
    const canvas = document.getElementById(canvasId);
    const empty = document.getElementById(emptyId);
    const hasData = Array.isArray(labels) && labels.length > 0 && (values || []).some(v => Number(v) > 0);

    if (!canvas || !empty) return false;

    if (hasData) {
      canvas.style.display = 'block';
      empty.style.display = 'none';
      return true;
    } else {
      canvas.style.display = 'none';
      empty.style.display = 'flex';
      return false;
    }
  }

  // Helper: colores
  function palette(n) {
    const base = [
      '#4A008B','#7B1FA2','#9575CD','#BA68C8',
      '#6A1B9A','#8E24AA','#AB47BC','#CE93D8'
    ];
    const out = [];
    for (let i=0; i<n; i++) out.push(base[i % base.length]);
    return out;
  }

  // Chart.js defaults para que NO crezcan infinito
  Chart.defaults.responsive = true;
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.plugins.legend.position = 'bottom';

  // --- Barras: stock por categoría
  (function initBar() {
    const data = (CH.bar_stock_categoria || {});
    const labels = data.labels || [];
    const values = data.values || [];

    if (!showEmptyIfNeeded('barCategorias','empty-barCategorias', labels, values)) return;

    const ctx = document.getElementById('barCategorias').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Unidades',
          data: values,
          backgroundColor: palette(values.length),
          borderRadius: 6,
        }]
      },
      options: {
        scales: {
          x: { ticks: { autoSkip: true, maxRotation: 0 } },
          y: { beginAtZero: true }
        }
      }
    });
  })();

  // --- Donut: stock por proveedor
  (function initPie() {
    const data = (CH.pie_stock_proveedor || {});
    const labels = data.labels || [];
    const values = data.values || [];

    if (!showEmptyIfNeeded('pieProveedores','empty-pieProveedores', labels, values)) return;

    const ctx = document.getElementById('pieProveedores').getContext('2d');
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: palette(values.length)
        }]
      },
      options: {
        cutout: '60%',
        plugins: { legend: { position: 'right' } }
      }
    });
  })();

  // --- Línea: lotes por mes de vencimiento
  (function initLine() {
    const data = (CH.line_caducidad_mes || {});
    const labels = data.labels || [];
    const values = data.values || [];

    if (!showEmptyIfNeeded('lineCaducidad','empty-lineCaducidad', labels, values)) return;

    const ctx = document.getElementById('lineCaducidad').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Lotes',
          data: values,
          fill: false,
          tension: .3,
          borderWidth: 2,
          pointRadius: 3,
          borderColor: '#4A008B'
        }]
      },
      options: {
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  })();

  // Formateo bonito de KPIs (CLP / entero)
  document.querySelectorAll('.kpi-value').forEach(el => {
    const raw = Number(el.getAttribute('data-number') || 0);
    if (el.classList.contains('money')) {
      el.textContent = new Intl.NumberFormat('es-CL').format(Math.round(raw));
      el.insertAdjacentText('afterbegin', '$');
    } else {
      el.textContent = new Intl.NumberFormat('es-CL').format(Math.round(raw));
    }
  });
})();