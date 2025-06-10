document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/dashboard-metrics/')
        .then(response => response.json())
        .then(data => {
            const nombres = data.data.map(item => item.nombre);
            const stocks = data.data.map(item => item.stock);

            const ctx = document.getElementById('graficoStockPorCategoria').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: nombres,
                    datasets: [{
                        label: 'Stock Actual',
                        data: stocks,
                        backgroundColor: 'rgba(74, 0, 139, 0.6)',
                        borderColor: 'rgba(74, 0, 139, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#343A40',
                                font: {
                                    family: 'HankenGrotesk'
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#343A40'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#343A40'
                            }
                        }
                    }
                }
            });

            // También actualizamos las métricas de resumen
            document.getElementById('total-productos').textContent = data.totales.productos;
            document.getElementById('stock-total').textContent = data.totales.stock;
            document.getElementById('lotes-activos').textContent = data.totales.lotes;
        })
        .catch(error => {
            console.error('Error al cargar los datos del dashboard:', error);
        });
});