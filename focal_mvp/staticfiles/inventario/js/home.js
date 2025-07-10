document.addEventListener('DOMContentLoaded', () => {
  const canvasElement = document.getElementById('graficoStockPorCategoria');
  const dataScriptElement = document.getElementById('dashboard-data');

  if (!canvasElement || !dataScriptElement) {
    return;
  }

  try {
    const dashboardData = JSON.parse(dataScriptElement.textContent);

    // --- CORRECCIÓN: Verificamos si hay datos ANTES de intentar dibujar el gráfico ---
    if (!dashboardData || !dashboardData.labels || dashboardData.labels.length === 0) {
        // Si no hay datos, podemos ocultar el contenedor del gráfico o mostrar un mensaje.
        const graphContainer = document.querySelector('.dashboard-graphs');
        if (graphContainer) {
            graphContainer.innerHTML = '<p class="no-data-message">No hay datos de stock para mostrar en el gráfico.</p>';
        }
        return;
    }

    const ctx = canvasElement.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: dashboardData.labels,
        datasets: [{
          label: 'Stock Actual por Producto',
          data: dashboardData.data,
          backgroundColor: 'rgba(74, 0, 139, 0.7)',
          borderColor: 'rgba(74, 0, 139, 1)',
          borderWidth: 1,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
          },
          tooltip: {
            backgroundColor: '#333',
            titleFont: { size: 14 },
            bodyFont: { size: 12 },
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) { if (value % 1 === 0) { return value; } }
            }
          }
        }
      }
    });

  } catch (error) {
    console.error('Error al parsear los datos JSON del dashboard:', error);
  }
});