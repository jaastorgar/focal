// ===== DATOS CON LOCALSTORAGE =====
let transactions = JSON.parse(localStorage.getItem('focal_transactions')) || [];

const alerts = [
    { id: 1, message: 'Próximo pago de sueldos en 5 días', type: 'warning' },
    { id: 2, message: 'Factura #1234 vencida', type: 'danger' },
    { id: 3, message: 'Meta mensual alcanzada al 87%', type: 'info' }
];

// Función para guardar en localStorage
function saveTransactions() {
    localStorage.setItem('focal_transactions', JSON.stringify(transactions));
}

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
            
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
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

    btnAdd.addEventListener('click', () => {
        modal.classList.add('active');
        document.getElementById('transactionDate').valueAsDate = new Date();
    });

    const closeModal = () => {
        modal.classList.remove('active');
        form.reset();
    };

    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const newTransaction = {
            id: Date.now(), // Usar timestamp como ID único
            date: document.getElementById('transactionDate').value,
            description: document.getElementById('transactionDescription').value,
            category: document.getElementById('transactionCategory').value,
            amount: parseInt(document.getElementById('transactionAmount').value),
            type: document.getElementById('transactionType').value,
            status: document.getElementById('transactionType').value === 'expense' ? 'Pagado' : undefined
        };

        transactions.unshift(newTransaction);
        saveTransactions(); // Guardar en localStorage
        
        updateDashboard();
        initTables();
        initCharts();
        
        closeModal();
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
    const saldoActual = totals.resultado;
    
    document.getElementById('saldoActual').textContent = formatCurrency(saldoActual);
    document.getElementById('ingresosDelMes').textContent = formatCurrency(totals.ingresos);
    document.getElementById('gastosDelMes').textContent = formatCurrency(totals.gastos);
    document.getElementById('resultado').textContent = formatCurrency(totals.resultado);
    
    const resultadoEl = document.getElementById('resultado');
    resultadoEl.className = totals.resultado >= 0 ? 'kpi-value text-green' : 'kpi-value text-red';
    
    const metaMensual = 7000000;
    const progreso = totals.ingresos > 0 ? (totals.ingresos / metaMensual) * 100 : 0;
    document.getElementById('goalProgress').textContent = `${progreso.toFixed(1)}%`;
    document.getElementById('progressFill').style.width = `${Math.min(progreso, 100)}%`;
}

function renderAlerts() {
    const container = document.getElementById('alertsContainer');
    
    if (transactions.length === 0) {
        container.innerHTML = `
            <div class="alert info">
                No hay transacciones registradas. Haz clic en "Añadir Transacción" para comenzar.
            </div>
        `;
        return;
    }
    
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
    
    if (ingresos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 2rem; color: var(--muted-text);">
                    No hay ingresos registrados. Añade una nueva transacción de tipo "Ingreso".
                </td>
            </tr>
        `;
        return;
    }
    
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
    
    if (gastos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem; color: var(--muted-text);">
                    No hay gastos registrados. Añade una nueva transacción de tipo "Gasto".
                </td>
            </tr>
        `;
        return;
    }
    
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
        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: var(--muted-text);">
                        No se encontraron resultados para "${searchTerm}"
                    </td>
                </tr>
            `;
            return;
        }
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
        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: var(--muted-text);">
                        No se encontraron resultados para "${searchTerm}"
                    </td>
                </tr>
            `;
            return;
        }
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
        saveTransactions(); // Guardar cambios
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

    const incomeByCategory = transactions
        .filter(t => t.type === 'income')
        .reduce((acc, transaction) => {
            const { category, amount } = transaction;
            if (!acc[category]) {
                acc[category] = 0;
            }
            acc[category] += amount;
            return acc;
        }, {});

    const sortedCategories = Object.entries(incomeByCategory)
        .sort(([, a], [, b]) => b - a);

    if (sortedCategories.length === 0) {
        // Mostrar mensaje en canvas cuando no hay datos
        ctx.getContext('2d').font = '16px Arial';
        ctx.getContext('2d').fillStyle = '#666';
        ctx.getContext('2d').textAlign = 'center';
        ctx.getContext('2d').fillText('No hay datos de ingresos', ctx.width / 2, ctx.height / 2);
        return;
    }

    const chartLabels = sortedCategories.map(item => item[0]);
    const chartData = sortedCategories.map(item => item[1]);

    const data = {
        labels: chartLabels,
        datasets: [{
            data: chartData,
            backgroundColor: ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#e4e2f7']
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
                            return `${label}: ${value} (${percentage}%)`;
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

    const expensesByCategory = transactions
        .filter(t => t.type === 'expense')
        .reduce((acc, transaction) => {
            const { category, amount } = transaction;
            if (!acc[category]) {
                acc[category] = 0;
            }
            acc[category] += amount;
            return acc;
        }, {});

    const sortedCategories = Object.entries(expensesByCategory)
        .sort(([, a], [, b]) => b - a);

    if (sortedCategories.length === 0) {
        ctx.getContext('2d').font = '16px Arial';
        ctx.getContext('2d').fillStyle = '#666';
        ctx.getContext('2d').textAlign = 'center';
        ctx.getContext('2d').fillText('No hay datos de gastos', ctx.width / 2, ctx.height / 2);
        return;
    }

    const chartLabels = sortedCategories.map(item => item[0]);
    const chartData = sortedCategories.map(item => item[1]);

    const data = {
        labels: chartLabels,
        datasets: [{
            label: 'Monto',
            data: chartData,
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