// static/js/dashboard.js

function goBack() {
    window.location.href = "/select_chatbot";
}

function logout() {
    axios.get('/logout')
        .then(() => {
            window.location.href = "/";
        })
        .catch(error => {
            console.error('Erro ao fazer logout:', error);
        });
}

function loadDashboardData() {
    axios.get('/get_dashboard_data')
        .then(response => {
            const data = response.data;
            
            // Atualizar quantidade de logins
            document.getElementById('login-count').textContent = data.login_count;

            // Criar gráfico de scores
            const ctx = document.getElementById('scores-chart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Conversas com Lead', 'Conversas com IA', 'Avaliação da IA'],
                    datasets: [{
                        label: 'Scores',
                        data: [data.lead_score, data.ia_conversation_score, data.ia_evaluation_score],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // Atualizar feedback da IA
            document.getElementById('ia-feedback').textContent = data.ia_feedback;

            // Atualizar posicionamento
            document.getElementById('posicionamento').textContent = data.posicionamento;
        })
        .catch(error => {
            console.error('Erro ao carregar dados do dashboard:', error);
        });
}

// Carregar dados do dashboard ao iniciar a página
window.onload = loadDashboardData;