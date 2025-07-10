// reports.js - Implements multiple chart types for reports section

document.addEventListener('DOMContentLoaded', () => {
    // Load all charts
    loadTopProductsChart();
    loadSalesTrendChart();
    loadDailySalesChart();
    loadRevenueOverviewChart();
    loadInventoryLevelsChart();
    loadWeeklySalesChart();
    loadMonthlySalesChart();
});

// Helper function to fetch JSON data from API
async function fetchData(url) {
    try {
        const response = await fetch(url, { credentials: 'include' });
        if (!response.ok) {
            console.error(`Failed to fetch ${url}: ${response.statusText}`);
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${url}:`, error);
        return null;
    }
}

// Chart instances
let topProductsChart, salesTrendChart, dailyChart, revenueChart, inventoryChart, weeklyChart, monthlyChart;

// Load Top Products Chart (Bar Chart)
async function loadTopProductsChart() {
    const data = await fetchData('/api/top-products/');
    if (!data) return;

    const ctx = document.getElementById('topProductsChart').getContext('2d');
    if (topProductsChart) topProductsChart.destroy();

    topProductsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Quantity Sold',
                data: data.map(item => item.quantity),
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Load Sales Trend Chart (Line Chart)
async function loadSalesTrendChart() {
    const data = await fetchData('/api/sales-trend/');
    if (!data) return;

    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    if (salesTrendChart) salesTrendChart.destroy();

    salesTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.date),
            datasets: [{
                label: 'Sales',
                data: data.map(item => item.total),
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.3)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Load Daily Sales Chart (Pie Chart)
async function loadDailySalesChart() {
    const data = await fetchData('/api/daily-sales/');
    if (!data) return;

    const ctx = document.getElementById('dailyChart').getContext('2d');
    if (dailyChart) dailyChart.destroy();

    dailyChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(item => item.product),
            datasets: [{
                label: 'Daily Sales',
                data: data.map(item => item.quantity),
                backgroundColor: generateColors(data.length),
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'right' } }
        }
    });
}

// Load Revenue Overview Chart (Doughnut Chart)
async function loadRevenueOverviewChart() {
    const data = await fetchData('/api/revenue-overview/');
    if (!data) return;

    const ctx = document.getElementById('revenueChart').getContext('2d');
    if (revenueChart) revenueChart.destroy();

    revenueChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.category),
            datasets: [{
                label: 'Revenue',
                data: data.map(item => item.amount),
                backgroundColor: generateColors(data.length),
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

// Load Inventory Levels Chart (Horizontal Bar Chart)
async function loadInventoryLevelsChart() {
    const data = await fetchData('/api/inventory-levels/');
    if (!data) return;

    const ctx = document.getElementById('inventoryChart').getContext('2d');
    if (inventoryChart) inventoryChart.destroy();

    inventoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                label: 'Stock Quantity',
                data: data.map(item => item.quantity),
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

// Load Weekly Sales Chart (Line Chart)
async function loadWeeklySalesChart() {
    const data = await fetchData('/api/weekly-sales/');
    if (!data) return;

    const ctx = document.getElementById('weeklyChart').getContext('2d');
    if (weeklyChart) weeklyChart.destroy();

    weeklyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.week),
            datasets: [{
                label: 'Weekly Sales',
                data: data.map(item => item.total),
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.3)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Load Monthly Sales Chart (Bar Chart)
async function loadMonthlySalesChart() {
    const data = await fetchData('/api/monthly-sales/');
    if (!data) return;

    const ctx = document.getElementById('monthlyChart').getContext('2d');
    if (monthlyChart) monthlyChart.destroy();

    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.month),
            datasets: [{
                label: 'Monthly Sales',
                data: data.map(item => item.total),
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Utility function to generate array of colors
function generateColors(count) {
    const colors = [
        '#667eea', '#764ba2', '#6a11cb', '#2575fc', '#1e3c72',
        '#ff6a00', '#ee0979', '#ff512f', '#dd2476', '#ff6f91',
        '#00c6ff', '#0072ff', '#00f260', '#0575e6', '#00b09b'
    ];
    let result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}
