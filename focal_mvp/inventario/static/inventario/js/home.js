document.addEventListener('DOMContentLoaded', () => {
  // 1. Buscamos el elemento canvas para el gráfico.
  const canvasElement = document.getElementById('graficoStockPorCategoria');
  if (!canvasElement) {
    console.error('Error: No se encontró el elemento canvas para el gráfico.');
    return;
  }

  // 2. Buscamos la etiqueta <script> que contiene nuestros datos.
  const dataScriptElement = document.getElementById('dashboard-data');
  if (!dataScriptElement) {
    console.error('Error: No se encontró la etiqueta de datos del dashboard.');
    return;
  }

  try {
    // 3. Extraemos y parseamos los datos JSON.
    // La vista de Django ya ha colocado los datos aquí.
    const dashboardData = JSON.parse(dataScriptElement.textContent);

    // Verificamos que los datos necesarios para el gráfico existan.
    if (!dashboardData || !dashboardData.labels || !dashboardData.data) {
        console.warn('Advertencia: Faltan datos para renderizar el gráfico del dashboard.');
        return;
    }

    // 4. Creamos el gráfico con los datos obtenidos.
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
              // Formatear los ticks para que no tengan decimales si son enteros
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