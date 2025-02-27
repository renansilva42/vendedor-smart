// app/static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    const backBtn = document.getElementById('back-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const updateAnalysisBtn = document.getElementById('update-analysis-btn');
    const loginCountElement = document.getElementById('login-count');
    const iaFeedbackElement = document.getElementById('ia-feedback');
    const posicionamentoElement = document.getElementById('posicionamento');
    const analysisSummaryElement = document.getElementById('analysis-summary');
    
    let scoresChart = null;
    
    // Event listeners
    backBtn.addEventListener('click', function() {
      window.location.href = '/select_chatbot';
    });
    
    logoutBtn.addEventListener('click', function() {
      window.location.href = '/logout';
    });
    
    updateAnalysisBtn.addEventListener('click', function() {
      updateAnalysisBtn.disabled = true;
      updateAnalysisBtn.textContent = 'Gerando análise...';
      analysisSummaryElement.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
      
      fetch('/generate_analysis')
        .then(response => response.json())
        .then(data => {
          if (data.summary) {
            analysisSummaryElement.innerHTML = data.summary;
          } else if (data.error) {
            analysisSummaryElement.innerHTML = `<p class="error-message">Erro: ${data.error}</p>`;
          }
        })
        .catch(error => {
          console.error('Erro ao gerar análise:', error);
          analysisSummaryElement.innerHTML = '<p class="error-message">Erro ao gerar análise. Tente novamente.</p>';
        })
        .finally(() => {
          updateAnalysisBtn.disabled = false;
          updateAnalysisBtn.textContent = 'Atualizar análise';
        });
    });
    
    // Carregar dados do dashboard
    loadDashboardData();
    
    function loadDashboardData() {
      fetch('/get_dashboard_data')
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            console.error('Erro ao carregar dados:', data.error);
            return;
          }
          
          // Atualizar contagem de logins
          loginCountElement.textContent = data.login_count || 0;
          
          // Atualizar feedback da IA
          iaFeedbackElement.textContent = data.ia_feedback || 'Nenhum feedback disponível';
          
          // Atualizar posicionamento
          posicionamentoElement.textContent = data.posicionamento || 'Nenhuma análise disponível';
          
          // Criar gráfico de scores
          createScoresChart(
            data.lead_score || 0,
            data.ia_conversation_score || 0,
            data.ia_evaluation_score || 0
          );
        })
        .catch(error => {
          console.error('Erro ao carregar dados do dashboard:', error);
        });
    }
    
    function createScoresChart(leadScore, conversationScore, evaluationScore) {
      const ctx = document.getElementById('scores-chart').getContext('2d');
      
      // Destruir gráfico existente se houver
      if (scoresChart) {
        scoresChart.destroy();
      }
      
      scoresChart = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: ['Pontuação de Lead', 'Pontuação de Conversa', 'Pontuação de Avaliação'],
          datasets: [{
            label: 'Scores',
            data: [leadScore, conversationScore, evaluationScore],
            backgroundColor: 'rgba(58, 110, 165, 0.2)',
            borderColor: 'rgba(58, 110, 165, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(58, 110, 165, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(58, 110, 165, 1)'
          }]
        },
        options: {
          scales: {
            r: {
              angleLines: {
                display: true
              },
              suggestedMin: 0,
              suggestedMax: 100
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw}/100`;
                }
              }
            }
          },
          responsive: true,
          maintainAspectRatio: true
        }
      });
    }
  });