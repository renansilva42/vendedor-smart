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
      axios.get('/logout')
          .then(() => {
              window.location.href = '/';
          })
          .catch(error => {
              console.error('Erro ao fazer logout:', error);
          });
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
  
  // Função para simular o carregamento com progresso
  function simulateLoading(elementId, callback) {
      const loadingBar = document.getElementById(elementId);
      const loadingText = loadingBar.querySelector('.loading-bar-text');
      let width = 0;
      
      // Intervalo para simular o carregamento
      const interval = setInterval(() => {
          if (width >= 100) {
              clearInterval(interval);
              if (callback) setTimeout(callback, 300); // Pequeno atraso para mostrar 100%
          } else {
              // Incremento aleatório para simular carregamento real
              width += Math.floor(Math.random() * 5) + 1;
              if (width > 100) width = 100;
              loadingBar.style.width = width + '%';
              loadingText.textContent = width + '%';
          }
      }, 100);
  }
  
  // Iniciar simulação de carregamento quando a página carregar
  // Simular carregamento para Quantidade de Logins
  simulateLoading('login-count-loading-bar', () => {
      // Após completar o carregamento, buscar os dados reais
      fetchLoginCount();
  });
  
  // Simular carregamento para Feedback da IA
  simulateLoading('ia-feedback-loading-bar', () => {
      fetchIAFeedback();
  });
  
  // Simular carregamento para Posicionamento
  simulateLoading('posicionamento-loading-bar', () => {
      fetchPosicionamento();
  });
  
  // Funções para buscar dados reais
  function fetchLoginCount() {
      fetch('/get_dashboard_data')
          .then(response => response.json())
          .then(data => {
              if (data.error) {
                  console.error('Erro ao carregar dados:', data.error);
                  return;
              }
              
              // Atualizar contagem de logins
              loginCountElement.innerHTML = `<h3>${data.login_count || 0}</h3>`;
              
              // Criar gráfico de scores
              createScoresChart(
                  data.lead_score || 0,
                  data.ia_conversation_score || 0,
                  data.ia_evaluation_score || 0
              );
          })
          .catch(error => {
              console.error('Erro ao carregar dados do dashboard:', error);
              loginCountElement.innerHTML = '<p class="error-message">Erro ao carregar dados</p>';
          });
  }
  
  function fetchIAFeedback() {
      fetch('/get_dashboard_data')
          .then(response => response.json())
          .then(data => {
              if (data.error) {
                  console.error('Erro ao carregar feedback:', data.error);
                  return;
              }
              
              // Atualizar feedback da IA
              iaFeedbackElement.innerHTML = `<p>${data.ia_feedback || 'Nenhum feedback disponível'}</p>`;
          })
          .catch(error => {
              console.error('Erro ao carregar feedback da IA:', error);
              iaFeedbackElement.innerHTML = '<p class="error-message">Erro ao carregar feedback</p>';
          });
  }
  
  function fetchPosicionamento() {
      fetch('/get_dashboard_data')
          .then(response => response.json())
          .then(data => {
              if (data.error) {
                  console.error('Erro ao carregar posicionamento:', data.error);
                  return;
              }
              
              // Atualizar posicionamento
              posicionamentoElement.innerHTML = `<p>${data.posicionamento || 'Nenhuma análise disponível'}</p>`;
          })
          .catch(error => {
              console.error('Erro ao carregar posicionamento:', error);
              posicionamentoElement.innerHTML = '<p class="error-message">Erro ao carregar posicionamento</p>';
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