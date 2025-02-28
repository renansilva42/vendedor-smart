// dashboard.js - Funcionalidades do dashboard interativo
document.addEventListener('DOMContentLoaded', function() {
  // Inicialização
  initDashboard();
  setupDraggableItems();
  setupToggleButtons();
  setupPeriodSelector();
  setupResetLayout();
  
  // Carregar dados iniciais
  loadDashboardData();
  
  // Event listeners
  document.getElementById('update-analysis-btn').addEventListener('click', updateAnalysis);
  document.getElementById('sentiment-filter').addEventListener('change', filterMessages);
  document.getElementById('topic-filter').addEventListener('change', filterMessages);
  document.getElementById('back-btn').addEventListener('click', () => window.location.href = '/select_chatbot');
  document.getElementById('logout-btn').addEventListener('click', () => window.location.href = '/logout');
});

// Configuração inicial do dashboard
function initDashboard() {
  // Configurar layout baseado em preferências salvas ou padrão
  const savedLayout = localStorage.getItem('dashboardLayout');
  if (savedLayout) {
      try {
          const layoutConfig = JSON.parse(savedLayout);
          applyLayout(layoutConfig);
      } catch (e) {
          console.error('Erro ao carregar layout salvo:', e);
          // Usar layout padrão em caso de erro
          resetLayout();
      }
  }
}

// Configurar itens arrastáveis
function setupDraggableItems() {
  const grid = document.getElementById('dashboard-grid');
  new Sortable(grid, {
      animation: 150,
      handle: '.dashboard-item-header',
      ghostClass: 'sortable-ghost',
      onEnd: function() {
          // Salvar nova ordem no localStorage
          saveCurrentLayout();
      }
  });
}

// Configurar botões de minimizar/expandir
function setupToggleButtons() {
  document.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', function() {
          const item = this.closest('.dashboard-item');
          const content = item.querySelector('.dashboard-item-content');
          const icon = this.querySelector('i');
          
          if (content.style.display === 'none') {
              content.style.display = 'block';
              icon.classList.remove('fa-chevron-down');
              icon.classList.add('fa-chevron-up');
          } else {
              content.style.display = 'none';
              icon.classList.remove('fa-chevron-up');
              icon.classList.add('fa-chevron-down');
          }
          
          // Salvar estado no localStorage
          saveItemState(item.dataset.id, content.style.display !== 'none');
      });
  });
  
  // Aplicar estados salvos
  restoreItemStates();
}

// Configurar seletor de período
function setupPeriodSelector() {
  const periodSelect = document.getElementById('period-select');
  periodSelect.addEventListener('change', function() {
      loadDashboardData(this.value);
  });
}

// Configurar botão de reset de layout
function setupResetLayout() {
  document.getElementById('reset-layout-btn').addEventListener('click', resetLayout);
}

// Salvar layout atual
function saveCurrentLayout() {
  const items = document.querySelectorAll('.dashboard-item');
  const layout = Array.from(items).map(item => ({
      id: item.dataset.id,
      expanded: item.querySelector('.dashboard-item-content').style.display !== 'none'
  }));
  
  localStorage.setItem('dashboardLayout', JSON.stringify(layout));
}

// Salvar estado de um item específico
function saveItemState(itemId, expanded) {
  const savedLayout = localStorage.getItem('dashboardLayout');
  if (savedLayout) {
      try {
          const layout = JSON.parse(savedLayout);
          const itemIndex = layout.findIndex(item => item.id === itemId);
          if (itemIndex !== -1) {
              layout[itemIndex].expanded = expanded;
              localStorage.setItem('dashboardLayout', JSON.stringify(layout));
          }
      } catch (e) {
          console.error('Erro ao salvar estado do item:', e);
      }
  }
}

// Restaurar estados dos itens
function restoreItemStates() {
  const savedLayout = localStorage.getItem('dashboardLayout');
  if (savedLayout) {
      try {
          const layout = JSON.parse(savedLayout);
          layout.forEach(item => {
              const domItem = document.querySelector(`.dashboard-item[data-id="${item.id}"]`);
              if (domItem) {
                  const content = domItem.querySelector('.dashboard-item-content');
                  const icon = domItem.querySelector('.toggle-btn i');
                  
                  if (!item.expanded) {
                      content.style.display = 'none';
                      icon.classList.remove('fa-chevron-up');
                      icon.classList.add('fa-chevron-down');
                  }
              }
          });
      } catch (e) {
          console.error('Erro ao restaurar estados dos itens:', e);
      }
  }
}

// Aplicar layout específico
function applyLayout(layoutConfig) {
  const grid = document.getElementById('dashboard-grid');
  
  // Reordenar itens
  layoutConfig.forEach(itemConfig => {
      const item = document.querySelector(`.dashboard-item[data-id="${itemConfig.id}"]`);
      if (item) {
          grid.appendChild(item);
      }
  });
}

// Resetar layout para o padrão
function resetLayout() {
  const grid = document.getElementById('dashboard-grid');
  const items = Array.from(document.querySelectorAll('.dashboard-item'));
  
  // Ordenar por prioridade
  items.sort((a, b) => parseInt(a.dataset.priority) - parseInt(b.dataset.priority));
  
  // Reordenar no DOM
  items.forEach(item => {
      grid.appendChild(item);
      
      // Expandir todos os itens
      const content = item.querySelector('.dashboard-item-content');
      const icon = item.querySelector('.toggle-btn i');
      content.style.display = 'block';
      icon.classList.remove('fa-chevron-down');
      icon.classList.add('fa-chevron-up');
  });
  
  // Limpar layout salvo
  localStorage.removeItem('dashboardLayout');
}

// Carregar dados do dashboard
function loadDashboardData(period = 'month') {
  showLoadingIndicators();
  
  axios.get(`/get_dashboard_data?period=${period}`)
      .then(response => {
          if (response.data.error) {
              console.error('Erro ao carregar dados:', response.data.error);
              return;
          }
          
          updateLoginCount(response.data.login_count);
          updateScoresChart(response.data.scores);
          updateIAFeedback(response.data.ia_feedback);
          updatePositioning(response.data.posicionamento);
          
          hideLoadingIndicators();
      })
      .catch(error => {
          console.error('Erro na requisição:', error);
          hideLoadingIndicators();
      });
}

// Mostrar indicadores de carregamento
function showLoadingIndicators() {
  document.querySelectorAll('.loading-bar-container').forEach(container => {
      container.style.display = 'block';
  });
}

// Esconder indicadores de carregamento
function hideLoadingIndicators() {
  document.querySelectorAll('.loading-bar-container').forEach(container => {
      container.style.display = 'none';
  });
}

// Atualizar contagem de logins
function updateLoginCount(count) {
  const container = document.getElementById('login-count');
  container.innerHTML = `<div class="metric-value">${count}</div>`;
  
  // Adicionar tendência (exemplo)
  const trendElement = document.getElementById('login-trend');
  const trendValue = Math.floor(Math.random() * 20) - 10; // Simulação
  
  if (trendValue > 0) {
      trendElement.innerHTML = `<i class="fas fa-arrow-up trend-up"></i> ${trendValue}% vs. período anterior`;
      trendElement.className = 'trend-up';
  } else if (trendValue < 0) {
      trendElement.innerHTML = `<i class="fas fa-arrow-down trend-down"></i> ${Math.abs(trendValue)}% vs. período anterior`;
      trendElement.className = 'trend-down';
  } else {
      trendElement.innerHTML = `<i class="fas fa-equals trend-neutral"></i> Sem alteração vs. período anterior`;
      trendElement.className = 'trend-neutral';
  }
}

// Atualizar gráfico de scores
function updateScoresChart(scores) {
  const ctx = document.getElementById('scores-chart').getContext('2d');
  
  // Destruir gráfico existente se houver
  if (window.scoresChart) {
      window.scoresChart.destroy();
  }
  
  // Dados para o gráfico
  const data = {
      labels: ['Clareza', 'Persuasão', 'Conhecimento', 'Empatia', 'Resolução'],
      datasets: [{
          label: 'Pontuação',
          data: [
              scores.clareza,
              scores.persuasao,
              scores.conhecimento,
              scores.empatia,
              scores.resolucao
          ],
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(54, 162, 235, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
          pointRadius: 5,
          pointHoverRadius: 7
      }]
  };
  
  // Configuração do gráfico
  const config = {
      type: 'radar',
      data: data,
      options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
              r: {
                  angleLines: {
                      display: true,
                      color: 'rgba(0, 0, 0, 0.1)'
                  },
                  ticks: {
                      beginAtZero: true,
                      max: 100,
                      stepSize: 20,
                      backdropColor: 'transparent',
                      font: {
                          size: 12,
                          weight: 'bold'
                      }
                  },
                  pointLabels: {
                      font: {
                          size: 14,
                          weight: 'bold'
                      }
                  }
              }
          },
          plugins: {
              tooltip: {
                  callbacks: {
                      title: function(tooltipItems) {
                          return tooltipItems[0].label;
                      },
                      label: function(context) {
                          return `Pontuação: ${context.raw}/100`;
                      },
                      afterLabel: function(context) {
                          const descriptions = {
                              'Clareza': 'Capacidade de comunicar ideias de forma clara e direta',
                              'Persuasão': 'Habilidade de convencer e influenciar decisões',
                              'Conhecimento': 'Domínio sobre produtos, serviços e mercado',
                              'Empatia': 'Capacidade de entender e responder às necessidades do cliente',
                              'Resolução': 'Eficácia na resolução de problemas e objeções'
                          };
                          return descriptions[context.label];
                      }
                  }
              },
              legend: {
                  display: false
              },
              datalabels: {
                  display: true,
                  color: '#000',
                  font: {
                      weight: 'bold'
                  },
                  formatter: function(value) {
                      return value;
                  }
              }
          }
      },
      plugins: [ChartDataLabels]
  };
  
  // Criar gráfico
  window.scoresChart = new Chart(ctx, config);
  
  // Atualizar legenda personalizada
  updateScoresLegend(data.labels, data.datasets[0].data);
  
  // Atualizar comparativo
  updateScoresComparison(scores);
}

// Atualizar legenda personalizada
function updateScoresLegend(labels, values) {
  const legendContainer = document.getElementById('scores-legend');
  legendContainer.innerHTML = '';
  
  labels.forEach((label, index) => {
      const item = document.createElement('div');
      item.className = 'legend-item';
      
      const colorBox = document.createElement('span');
      colorBox.className = 'legend-color';
      colorBox.style.backgroundColor = 'rgba(54, 162, 235, 1)';
      
      const labelText = document.createElement('span');
      labelText.className = 'legend-label';
      labelText.textContent = `${label}: ${values[index]}`;
      
      item.appendChild(colorBox);
      item.appendChild(labelText);
      legendContainer.appendChild(item);
  });
}

// Atualizar comparativo de scores
function updateScoresComparison(scores) {
  const container = document.getElementById('scores-comparison');
  
  // Simulação de dados do período anterior
  const previousScores = {
      clareza: Math.max(0, scores.clareza + (Math.floor(Math.random() * 20) - 10)),
      persuasao: Math.max(0, scores.persuasao + (Math.floor(Math.random() * 20) - 10)),
      conhecimento: Math.max(0, scores.conhecimento + (Math.floor(Math.random() * 20) - 10)),
      empatia: Math.max(0, scores.empatia + (Math.floor(Math.random() * 20) - 10)),
      resolucao: Math.max(0, scores.resolucao + (Math.floor(Math.random() * 20) - 10))
  };
  
  // Calcular diferenças
  const differences = {
      clareza: scores.clareza - previousScores.clareza,
      persuasao: scores.persuasao - previousScores.persuasao,
      conhecimento: scores.conhecimento - previousScores.conhecimento,
      empatia: scores.empatia - previousScores.empatia,
      resolucao: scores.resolucao - previousScores.resolucao
  };
  
  // Criar HTML para comparativo
  let html = '<div class="comparison-grid">';
  
  Object.entries(differences).forEach(([key, diff]) => {
      const label = key.charAt(0).toUpperCase() + key.slice(1);
      const className = diff > 0 ? 'trend-up' : (diff < 0 ? 'trend-down' : 'trend-neutral');
      const icon = diff > 0 ? 'fa-arrow-up' : (diff < 0 ? 'fa-arrow-down' : 'fa-equals');
      
      html += `
          <div class="comparison-item">
              <span class="comparison-label">${label}</span>
              <span class="comparison-value ${className}">
                  <i class="fas ${icon}"></i> ${Math.abs(diff)}
              </span>
          </div>
      `;
  });
  
  html += '</div>';
  container.innerHTML = html;
}

// Atualizar feedback da IA
function updateIAFeedback(feedback) {
  const container = document.getElementById('ia-feedback');
  container.innerHTML = `<div class="feedback-content">${feedback}</div>`;
}

// Atualizar posicionamento
function updatePositioning(posicionamento) {
  const container = document.getElementById('posicionamento');
  const guideContainer = document.getElementById('posicionamento-guide');
  
  if (posicionamento.includes("não há mensagens suficientes")) {
      // Mostrar guia de próximos passos
      container.innerHTML = '';
      guideContainer.style.display = 'block';
      
      // Atualizar progresso (simulação)
      const progress = Math.floor(Math.random() * 60); // 0-60%
      document.getElementById('analysis-progress').style.width = `${progress}%`;
      document.getElementById('analysis-progress').textContent = `${progress}%`;
      
      // Atualizar número de conversas necessárias (simulação)
      const requiredConversations = Math.floor(Math.random() * 10) + 3;
      document.getElementById('required-conversations').textContent = requiredConversations;
  } else {
      // Mostrar análise de posicionamento
      container.innerHTML = `<div class="positioning-content">${posicionamento}</div>`;
      guideContainer.style.display = 'none';
  }
}

// Atualizar análise de mensagens
function updateAnalysis() {
  const button = document.getElementById('update-analysis-btn');
  const container = document.getElementById('analysis-summary');
  
  // Alterar estado do botão
  button.disabled = true;
  button.textContent = 'Atualizando...';
  
  axios.get('/generate_analysis')
      .then(response => {
          if (response.data.error) {
              console.error('Erro ao gerar análise:', response.data.error);
              container.innerHTML = `<div class="error-message">Erro ao gerar análise: ${response.data.error}</div>`;
              return;
          }
          
          // Processar e exibir mensagens
          displayChatMessages(response.data.summary);
          
          // Gerar análise de sentimento (simulação)
          generateSentimentAnalysis();
          
          // Gerar tópicos recorrentes (simulação)
          generateTopicsAnalysis();
          
          // Preencher filtro de tópicos
          populateTopicFilter();
      })
      .catch(error => {
          console.error('Erro na requisição:', error);
          container.innerHTML = `<div class="error-message">Erro na requisição: ${error.message}</div>`;
      })
      .finally(() => {
          // Restaurar estado do botão
          button.disabled = false;
          button.textContent = 'Atualizar análise';
      });
}

// Exibir mensagens de chat
function displayChatMessages(htmlContent) {
  const chatContainer = document.getElementById('chat-messages');
  
  // Verificar se o conteúdo é HTML
  if (htmlContent.includes('<')) {
      chatContainer.innerHTML = htmlContent;
  } else {
      // Processar mensagens de texto simples
      const messages = htmlContent.split('\n');
      let html = '';
      
      messages.forEach(message => {
          if (message.trim()) {
              // Tentar identificar remetente
              const parts = message.split(':');
              if (parts.length >= 2) {
                  const sender = parts[0].trim();
                  const content = parts.slice(1).join(':').trim();
                  const timestamp = new Date().toLocaleTimeString();
                  const messageClass = sender.toLowerCase().includes('prof') ? 'message-sent' : 'message-received';
                  
                  html += `
                      <div class="chat-message ${messageClass}" data-sentiment="neutral">
                          <div class="message-header">
                              <span class="message-sender">${sender}</span>
                              <span class="message-time">${timestamp}</span>
                          </div>
                          <div class="message-body">${content}</div>
                      </div>
                  `;
              } else {
                  html += `<div class="chat-message">${message}</div>`;
              }
          }
      });
      
      chatContainer.innerHTML = html;
  }
  
  // Adicionar atributos de sentimento aleatórios para demonstração
  const sentiments = ['positive', 'neutral', 'negative'];
  const messages = document.querySelectorAll('.chat-message');
  
  messages.forEach(message => {
      const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
      message.dataset.sentiment = randomSentiment;
      message.classList.add(`sentiment-${randomSentiment}`);
  });
}

// Filtrar mensagens com base nos seletores
function filterMessages() {
  const sentimentFilter = document.getElementById('sentiment-filter').value;
  const topicFilter = document.getElementById('topic-filter').value;
  
  const messages = document.querySelectorAll('.chat-message');
  
  messages.forEach(message => {
      const messageSentiment = message.dataset.sentiment;
      const messageTopic = message.dataset.topic;
      
      let shouldShow = true;
      
      if (sentimentFilter !== 'all' && messageSentiment !== sentimentFilter) {
          shouldShow = false;
      }
      
      if (topicFilter !== 'all' && messageTopic !== topicFilter) {
          shouldShow = false;
      }
      
      message.style.display = shouldShow ? 'block' : 'none';
  });
}

// Gerar análise de sentimento (simulação)
function generateSentimentAnalysis() {
  const sentimentChart = document.getElementById('sentiment-chart');
  
  // Destruir gráfico existente se houver
  if (window.sentimentChart) {
      window.sentimentChart.destroy();
  }
  
  // Dados simulados
  const data = {
      labels: ['Positivo', 'Neutro', 'Negativo'],
      datasets: [{
          data: [65, 25, 10],
          backgroundColor: ['#4CAF50', '#FFC107', '#F44336'],
          borderWidth: 0
      }]
  };
  
  // Configuração do gráfico
  const config = {
      type: 'doughnut',
      data: data,
      options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
              legend: {
                  position: 'bottom',
                  labels: {
                      font: {
                          size: 12
                      }
                  }
              },
              tooltip: {
                  callbacks: {
                      label: function(context) {
                          return `${context.label}: ${context.raw}%`;
                      }
                  }
              }
          }
      }
  };
  
  // Criar gráfico
  window.sentimentChart = new Chart(sentimentChart, config);
  
  // Adicionar atributos de sentimento às mensagens (simulação)
  const messages = document.querySelectorAll('.chat-message');
  const sentiments = ['positive', 'neutral', 'negative'];
  const weights = [0.65, 0.25, 0.1]; // Probabilidades correspondentes aos percentuais
  
  messages.forEach(message => {
      // Selecionar sentimento com base nas probabilidades
      let random = Math.random();
      let sentimentIndex = 0;
      let cumulativeWeight = 0;
      
      for (let i = 0; i < weights.length; i++) {
          cumulativeWeight += weights[i];
          if (random <= cumulativeWeight) {
              sentimentIndex = i;
              break;
          }
      }
      
      const sentiment = sentiments[sentimentIndex];
      message.dataset.sentiment = sentiment;
      
      // Adicionar classe visual
      message.classList.add(`sentiment-${sentiment}`);
  });
}

// Gerar análise de tópicos (simulação)
function generateTopicsAnalysis() {
  const topicsList = document.getElementById('topics-list');
  
  // Tópicos simulados
  const topics = [
      { name: 'Preço', count: 12, percentage: 35 },
      { name: 'Entrega', count: 8, percentage: 23 },
      { name: 'Qualidade', count: 6, percentage: 17 },
      { name: 'Garantia', count: 5, percentage: 14 },
      { name: 'Suporte', count: 4, percentage: 11 }
  ];
  
  // Criar HTML para tópicos
  let html = '';
  
  topics.forEach(topic => {
      html += `
          <div class="topic-item">
              <div class="topic-header">
                  <span class="topic-name">${topic.name}</span>
                  <span class="topic-count">${topic.count} mensagens</span>
              </div>
              <div class="topic-progress">
                  <div class="topic-progress-bar" style="width: ${topic.percentage}%"></div>
                  <span class="topic-percentage">${topic.percentage}%</span>
              </div>
          </div>
      `;
  });
  
  topicsList.innerHTML = html;
  
  // Adicionar atributos de tópico às mensagens (simulação)
  const messages = document.querySelectorAll('.chat-message');
  const topicNames = topics.map(t => t.name.toLowerCase());
  
  messages.forEach(message => {
      const randomIndex = Math.floor(Math.random() * topicNames.length);
      const topic = topicNames[randomIndex];
      message.dataset.topic = topic;
  });
}

// Preencher filtro de tópicos
function populateTopicFilter() {
  const topicFilter = document.getElementById('topic-filter');
  
  // Limpar opções existentes, exceto a primeira
  while (topicFilter.options.length > 1) {
      topicFilter.remove(1);
  }
  
  // Obter tópicos únicos das mensagens
  const messages = document.querySelectorAll('.chat-message');
  const topics = new Set();
  
  messages.forEach(message => {
      const topic = message.dataset.topic;
      if (topic) {
          topics.add(topic);
      }
  });
  
  // Adicionar opções ao filtro
  topics.forEach(topic => {
      const option = document.createElement('option');
      option.value = topic;
      option.textContent = topic.charAt(0).toUpperCase() + topic.slice(1);
      topicFilter.appendChild(option);
  });
}

// Adicionar CSS para o dashboard aprimorado
function addDashboardStyles() {
  const styleElement = document.createElement('style');
  styleElement.textContent = `
      /* Grid Layout */
      .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
          gap: 20px;
          margin-top: 20px;
      }
      
      /* Dashboard Items */
      .dashboard-item {
          background-color: var(--card-bg-color);
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          overflow: hidden;
          transition: all 0.3s ease;
      }
      
      .dashboard-item:hover {
          box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
      }
      
      .dashboard-item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          border-bottom: 1px solid var(--border-color);
      }
      
      .dashboard-item-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
      }
      
      .dashboard-item-controls {
          display: flex;
          gap: 10px;
      }
      
      .dashboard-item-content {
          padding: 20px;
      }
      
      /* Toggle Button */
      .toggle-btn {
          background: none;
          border: none;
          cursor: pointer;
          color: var(--text-color);
          font-size: 16px;
          padding: 5px;
          border-radius: 4px;
          transition: background-color 0.2s;
      }
      
      .toggle-btn:hover {
          background-color: var(--hover-color);
      }
      
      /* Chart Container */
      .chart-container {
          height: 300px;
          position: relative;
      }
      
      /* Legend */
      .chart-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 15px;
      }
      
      .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;
      }
      
      .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
      }
      
      /* Comparison */
      .chart-comparison {
          margin-top: 20px;
          border-top: 1px solid var(--border-color);
          padding-top: 15px;
      }
      
      .comparison-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 10px;
          margin-top: 10px;
      }
      
      .comparison-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
      }
      
      /* Metric Display */
      .metric-display {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 150px;
      }
      
      .metric-value {
          font-size: 64px;
          font-weight: 700;
          color: var(--primary-color);
      }
      
      .metric-trend {
          margin-top: 10px;
          text-align: center;
      }
      
      /* Trends */
      .trend-up {
          color: #4CAF50;
      }
      
      .trend-down {
          color: #F44336;
      }
      
      .trend-neutral {
          color: #FFC107;
      }
      
      /* Guide Container */
      .guide-container {
          background-color: var(--light-bg-color);
          border-radius: 8px;
          padding: 15px;
          margin-top: 10px;
      }
      
      .steps-list {
          margin: 10px 0;
          padding-left: 20px;
      }
      
      .progress-container {
          margin-top: 15px;
      }
      
      .progress-label {
          margin-bottom: 5px;
          font-weight: 500;
      }
      
      .progress-bar {
          height: 10px;
          background-color: var(--border-color);
          border-radius: 5px;
          overflow: hidden;
      }
      
      .progress-fill {
          height: 100%;
          background-color: var(--primary-color);
          border-radius: 5px;
          text-align: center;
          font-size: 10px;
          line-height: 10px;
          color: white;
      }
      
      /* Analysis Controls */
      .analysis-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
              }
        
        .analysis-filters {
            display: flex;
            gap: 10px;
        }
        
        /* Chat Container */
        .chat-container {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .chat-messages {
            padding: 10px;
        }
        
        .chat-message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 8px;
            position: relative;
        }
        
        .message-sent {
            background-color: var(--light-primary-color);
            margin-left: 20px;
        }
        
        .message-received {
            background-color: var(--light-bg-color);
            margin-right: 20px;
        }
        
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 12px;
        }
        
        .message-sender {
            font-weight: 600;
        }
        
        .message-time {
            color: var(--text-secondary-color);
        }
        
        .message-body {
            word-break: break-word;
        }
        
        /* Sentiment Analysis */
        .sentiment-analysis, .topics-analysis {
            margin-top: 20px;
        }
        
        .mini-chart {
            height: 150px;
            margin-top: 10px;
        }
        
        /* Topics List */
        .topics-list {
            margin-top: 10px;
        }
        
        .topic-item {
            margin-bottom: 10px;
        }
        
        .topic-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .topic-name {
            font-weight: 500;
        }
        
        .topic-count {
            font-size: 12px;
            color: var(--text-secondary-color);
        }
        
        .topic-progress {
            height: 8px;
            background-color: var(--border-color);
            border-radius: 4px;
            position: relative;
        }
        
        .topic-progress-bar {
            height: 100%;
            background-color: var(--primary-color);
            border-radius: 4px;
        }
        
        .topic-percentage {
            position: absolute;
            right: 0;
            top: -18px;
            font-size: 12px;
        }
        
        /* Sentiment Colors */
        .sentiment-positive {
            border-left: 3px solid #4CAF50;
        }
        
        .sentiment-neutral {
            border-left: 3px solid #FFC107;
        }
        
        .sentiment-negative {
            border-left: 3px solid #F44336;
        }
        
        /* Period Selector */
        .period-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .select-control {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            background-color: var(--input-bg-color);
            color: var(--text-color);
        }
        
        /* Responsive Adjustments */
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .header-buttons {
                margin-top: 10px;
            }
            
            .analysis-controls {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .analysis-filters {
                width: 100%;
            }
            
            .select-control {
                width: 100%;
            }
        }
    `;
    
    document.head.appendChild(styleElement);
}

// Executar ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar estilos
    addDashboardStyles();
});