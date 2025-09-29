// ===== DATOS DE EJEMPLO =====
let transactions = [
    { id: 1, date: '2025-09-15', description: 'Venta Servicio Premium', category: 'Ventas', amount: 2500000, type: 'income' },
    { id: 2, date: '2025-09-14', description: 'Consultoría Empresarial', category: 'Consultoría', amount: 1800000, type: 'income' },
    { id: 3, date: '2025-09-13', description: 'Pago Sueldos', category: 'Sueldos', amount: 3200000, type: 'expense', status: 'Pagado' },
    { id: 4, date: '2025-09-12', description: 'Campaña Facebook Ads', category: 'Marketing', amount: 450000, type: 'expense', status: 'Pagado' },
    { id: 5, date: '2025-09-10', description: 'Venta Curso Online', category: 'Ventas', amount: 980000, type: 'income' },
    { id: 6, date: '2025-09-08', description: 'Consultoría Digital', category: 'Consultoría', amount: 1200000, type: 'income' },
    { id: 7, date: '2025-09-05', description: 'Arriendo Oficina', category: 'Oficina', amount: 650000, type: 'expense', status: 'Pagado' }
];

const alerts = [
    { id: 1, message: 'Próximo pago de sueldos en 5 días', type: 'warning' },
    { id: 2, message: 'Factura #1234 vencida', type: 'danger' },
    { id: 3, message: 'Meta mensual alcanzada al 87%', type: 'info' }
];

// ===== UTILIDADES =====
const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0
    }).format(value);
};

const calculateTotals = () => {
    const ingresos = transactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);
    
    const gastos = transactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);
    
    return { ingresos, gastos, resultado: ingresos - gastos };
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initModal();
    initDashboard();
    initTables();
    initCharts();
    renderAlerts();
});

// ===== NAVEGACIÓN =====
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.section');

    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            
            // Actualizar botones activos
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            // Mostrar sección correspondiente
            sections.forEach(section => section.classList.remove('active'));
            document.getElementById(`section-${sectionId}`).classList.add('active');
        });
    });
}

// ===== MODAL =====
function initModal() {
    const modal = document.getElementById('modalTransaction');
    const btnAdd = document.getElementById('btnAddTransaction');
    const btnClose = document.getElementById('closeModal');
    const btnCancel = document.getElementById('cancelModal');
    const form = document.getElementById('formTransaction');

    // Abrir modal
    btnAdd.addEventListener('click', () => {
        modal.classList.add('active');
        // Establecer fecha actual por defecto
        document.getElementById('transactionDate').valueAsDate = new Date();
    });

    // Cerrar modal
    const closeModal = () => {
        modal.classList.remove('active');
        form.reset();
    };

    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);

    // Cerrar al hacer clic fuera del modal
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Enviar formulario
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const newTransaction = {
            id: transactions.length + 1,
            date: document.getElementById('transactionDate').value,
            description: document.getElementById('transactionDescription').value,
            category: document.getElementById('transactionCategory').value,
            amount: parseInt(document.getElementById('transactionAmount').value),
            type: document.getElementById('transactionType').value,
            status: document.getElementById('transactionType').value === 'expense' ? 'Pagado' : undefined
        };

        transactions.unshift(newTransaction);
        
        // Actualizar dashboard y tablas
        updateDashboard();
        initTables();
        initCharts();
        
        closeModal();
        
        // Mostrar mensaje de éxito (opcional)
        alert('Transacción agregada exitosamente');
    });
}

// ===== DASHBOARD =====
function initDashboard() {
    updateDashboard();
    renderAlerts();
}

function updateDashboard() {
    const totals = calculateTotals();
    const saldoActual = 8500000; // Esto podría ser calculado
    
    document.getElementById('saldoActual').textContent = formatCurrency(saldoActual);
    document.getElementById('ingresosDelMes').textContent = formatCurrency(totals.ingresos);
    document.getElementById('gastosDelMes').textContent = formatCurrency(totals.gastos);
    document.getElementById('resultado').textContent = formatCurrency(totals.resultado);
    
    // Actualizar clase de color para resultado
    const resultadoEl = document.getElementById('resultado');
    resultadoEl.className = totals.resultado >= 0 ? 'kpi-value text-green' : 'kpi-value text-red';
    
    // Actualizar meta
    const metaMensual = 7000000;
    const progreso = (totals.ingresos / metaMensual) * 100;
    document.getElementById('goalProgress').textContent = `${progreso.toFixed(1)}%`;
    document.getElementById('progressFill').style.width = `${Math.min(progreso, 100)}%`;
}

function renderAlerts() {
    const container = document.getElementById('alertsContainer');
    container.innerHTML = alerts.map(alert => `
        <div class="alert ${alert.type}">
            ${alert.message}
        </div>
    `).join('');
}

// ===== TABLAS =====
function initTables() {
    renderIngresosTable();
    renderGastosTable();
    initSearch();
}

function renderIngresosTable() {
    const tbody = document.getElementById('ingresosTable');
    const ingresos = transactions.filter(t => t.type === 'income');
    
    tbody.innerHTML = ingresos.map(transaction => `
        <tr>
            <td>${transaction.date}</td>
            <td>${transaction.description}</td>
            <td>
                <span class="badge badge-green">${transaction.category}</span>
            </td>
            <td class="text-right" style="font-weight: 600; color: var(--green-600);">
                ${formatCurrency(transaction.amount)}
            </td>
            <td class="text-center">
                <button class="action-btn" onclick="editTransaction(${transaction.id})">✏️</button>
                <button class="action-btn delete" onclick="deleteTransaction(${transaction.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function renderGastosTable() {
    const tbody = document.getElementById('gastosTable');
    const gastos = transactions.filter(t => t.type === 'expense');
    
    tbody.innerHTML = gastos.map(transaction => `
        <tr>
            <td>${transaction.date}</td>
            <td>${transaction.description}</td>
            <td>
                <span class="badge badge-red">${transaction.category}</span>
            </td>
            <td class="text-center">
                <span class="badge badge-green">${transaction.status}</span>
            </td>
            <td class="text-right" style="font-weight: 600; color: var(--red-600);">
                ${formatCurrency(transaction.amount)}
            </td>
            <td class="text-center">
                <button class="action-btn" onclick="attachFile(${transaction.id})">📎</button>
                <button class="action-btn" onclick="editTransaction(${transaction.id})">✏️</button>
                <button class="action-btn delete" onclick="deleteTransaction(${transaction.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function initSearch() {
    const searchIngresos = document.getElementById('searchIngresos');
    const searchGastos = document.getElementById('searchGastos');
    
    if (searchIngresos) {
        searchIngresos.addEventListener('input', (e) => {
            filterTable(e.target.value, 'income');
        });
    }
    
    if (searchGastos) {
        searchGastos.addEventListener('input', (e) => {
            filterTable(e.target.value, 'expense');
        });
    }
}

function filterTable(searchTerm, type) {
    const filtered = transactions.filter(t => 
        t.type === type && 
        (t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
         t.category.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    
    if (type === 'income') {
        const tbody = document.getElementById('ingresosTable');
        tbody.innerHTML = filtered.map(transaction => `
            <tr>
                <td>${transaction.date}</td>
                <td>${transaction.description}</td>
                <td><span class="badge badge-green">${transaction.category}</span></td>
                <td class="text-right" style="font-weight: 600; color: var(--green-600);">
                    ${formatCurrency(transaction.amount)}
                </td>
                <td class="text-center">
                    <button class="action-btn" onclick="editTransaction(${transaction.id})">✏️</button>
                    <button class="action-btn delete" onclick="deleteTransaction(${transaction.id})">🗑️</button>
                </td>
            </tr>
        `).join('');
    } else {
        const tbody = document.getElementById('gastosTable');
        tbody.innerHTML = filtered.map(transaction => `
            <tr>
                <td>${transaction.date}</td>
                <td>${transaction.description}</td>
                <td><span class="badge badge-red">${transaction.category}</span></td>
                <td class="text-center"><span class="badge badge-green">${transaction.status}</span></td>
                <td class="text-right" style="font-weight: 600; color: var(--red-600);">
                    ${formatCurrency(transaction.amount)}
                </td>
                <td class="text-center">
                    <button class="action-btn" onclick="attachFile(${transaction.id})">📎</button>
                    <button class="action-btn" onclick="editTransaction(${transaction.id})">✏️</button>
                    <button class="action-btn delete" onclick="deleteTransaction(${transaction.id})">🗑️</button>
                </td>
            </tr>
        `).join('');
    }
}

// ===== ACCIONES DE TABLA =====
function editTransaction(id) {
    alert(`Editar transacción ID: ${id}\n(Funcionalidad en desarrollo)`);
}

function deleteTransaction(id) {
    if (confirm('¿Estás seguro de eliminar esta transacción?')) {
        transactions = transactions.filter(t => t.id !== id);
        updateDashboard();
        initTables();
        initCharts();
    }
}

function attachFile(id) {
    alert(`Adjuntar archivo a transacción ID: ${id}\n(Funcionalidad en desarrollo)`);
}

// ===== GRÁFICOS =====
function initCharts() {
    createCashFlowChart();
    createIncomePieChart();
    createExpensesChart();
    createProjectionChart();
}

function createCashFlowChart() {
    const ctx = document.getElementById('cashFlowChart');
    if (!ctx) return;
    
    // Destruir gráfico anterior si existe
    if (window.cashFlowChartInstance) {
        window.cashFlowChartInstance.destroy();
    }
    
    const data = {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        datasets: [
            {
                label: 'Ingresos',
                data: [4500000, 5200000, 4800000, 5500000, 6200000, 5800000],
                backgroundColor: '#10b981'
            },
            {
                label: 'Gastos',
                data: [3200000, 3800000, 3500000, 4100000, 4300000, 3900000],
                backgroundColor: '#ef4444'
            }
        ]
    };
    
    window.cashFlowChartInstance = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000000) + 'M';
                        }
                    }
                }
            }
        }
    });
}

function createIncomePieChart() {
    const ctx = document.getElementById('incomePieChart');
    if (!ctx) return;
    
    if (window.incomePieChartInstance) {
        window.incomePieChartInstance.destroy();
    }
    
    const data = {
        labels: ['Ventas', 'Consultoría', 'Servicios', 'Otros'],
        datasets: [{
            data: [15000000, 8000000, 5000000, 2000000],
            backgroundColor: ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']
        }]
    };
    
    window.incomePieChartInstance = new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatCurrency(context.parsed);
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return label + ': ' + value + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function createExpensesChart() {
    const ctx = document.getElementById('expensesChart');
    if (!ctx) return;
    
    if (window.expensesChartInstance) {
        window.expensesChartInstance.destroy();
    }
    
    const data = {
        labels: ['Sueldos', 'Marketing', 'Oficina', 'Proveedores', 'Otros'],
        datasets: [{
            label: 'Monto',
            data: [8000000, 4500000, 2800000, 6200000, 1500000],
            backgroundColor: '#ef4444'
        }]
    };
    
    window.expensesChartInstance = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.x);
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000000) + 'M';
                        }
                    }
                }
            }
        }
    });
}

function createProjectionChart() {
    const ctx = document.getElementById('projectionChart');
    if (!ctx) return;
    
    if (window.projectionChartInstance) {
        window.projectionChartInstance.destroy();
    }
    
    const data = {
        labels: ['Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        datasets: [
            {
                label: 'Real',
                data: [5800000, 6100000, null, null, null, null],
                borderColor: '#8b5cf6',
                backgroundColor: '#8b5cf6',
                borderWidth: 3,
                tension: 0.4
            },
            {
                label: 'Proyectado',
                data: [null, null, 6500000, 7000000, 7200000, 7500000],
                borderColor: '#a78bfa',
                backgroundColor: '#a78bfa',
                borderWidth: 3,
                borderDash: [5, 5],
                tension: 0.4
            }
        ]
    };
    
    window.projectionChartInstance = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.parsed.y !== null) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000000) + 'M';
                        }
                    }
                }
            }
        }
    });
}