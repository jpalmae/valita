(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const chartElement = document.getElementById('orders-chart');
        if (!chartElement || typeof Chart === 'undefined') {
            return;
        }

        const labels = JSON.parse(chartElement.dataset.labels || '[]');
        const values = JSON.parse(chartElement.dataset.values || '[]');

        new Chart(chartElement, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Pedidos',
                    data: values,
                    borderColor: '#F28572',
                    backgroundColor: 'rgba(242, 133, 114, 0.15)',
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointBackgroundColor: '#F28572'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    });
})();
