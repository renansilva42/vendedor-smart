// app/static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const backBtn = document.getElementById('back-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const newUserBtn = document.getElementById('new-user-btn');
    
    let isProcessing = false;
    let userName = 'Usuário';
    
    // Carregar histórico de chat
    loadChatHistory();
    
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    backBtn.addEventListener('click', function() {
      window.location.href = '/select_chatbot';
    });
    
    logoutBtn.addEventListener('click', function() {
      window.location.href = '/logout';
    });
    
    newUserBtn.addEventListener('click', function() {
      if (confirm('Iniciar uma nova conversa? O histórico atual será mantido, mas você começará com um novo usuário.')) {
        startNewConversation();
      }
    });
    
    function loadChatHistory() {
      fetch('/get_chat_history')
        .then(response => response.json())
        .then(messages => {
          if (messages && messages.length > 0) {
            chatContainer.innerHTML = '';
            messages.forEach(msg => {
              if (msg.role === 'user') {
                addUserMessage(msg.content, msg.timestamp, msg.user_name);
                if (msg.user_name && msg.user_name !== 'Usuário Anônimo') {
                  userName = msg.user_name;
                }
              } else if (msg.role === 'assistant') {
                addAssistantMessage(msg.content, msg.timestamp);
              }
            });
            scrollToBottom();
          } else {
            addSystemMessage('Olá! Como posso ajudar você hoje?');
          }
        })
        .catch(error => {
          console.error('Erro ao carregar histórico:', error);
          addSystemMessage('Erro ao carregar histórico. Por favor, recarregue a página.');
        });
    }
    
    function sendMessage() {
      const message = userInput.value.trim();
      if (!message || isProcessing) return;
      
      isProcessing = true;
      
      // Adicionar mensagem do usuário à interface
      addUserMessage(message);
      userInput.value = '';
      
      // Mostrar indicador de carregamento
      const loadingId = 'loading-' + Date.now();
      addLoadingMessage(loadingId);
      
      // Enviar mensagem para o backend
      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          chatbot_type: chatbotType
        }),
      })
      .then(response => response.json())
      .then(data => {
        // Remover indicador de carregamento
        removeElement(loadingId);
        
        // Atualizar nome do usuário se necessário
        if (data.user_name && data.user_name !== userName && data.user_name !== 'Usuário Anônimo') {
          userName = data.user_name;
          // Atualizar nome em mensagens anteriores
          document.querySelectorAll('.chat-message--user .chat-message__sender').forEach(el => {
            el.textContent = userName;
          });
        }
        
        // Adicionar resposta do assistente
        addAssistantMessage(data.response);
        
        isProcessing = false;
      })
      .catch(error => {
        console.error('Erro:', error);
        removeElement(loadingId);
        addSystemMessage('Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.');
        isProcessing = false;
      });
    }
    
    function addUserMessage(message, timestamp = null, name = null) {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message chat-message--user';
      
      const senderDiv = document.createElement('div');
      senderDiv.className = 'chat-message__sender';
      senderDiv.textContent = name || userName;
      
      const contentDiv = document.createElement('div');
      contentDiv.className = 'chat-message__content';
      contentDiv.textContent = message;
      
      const timestampDiv = document.createElement('div');
      timestampDiv.className = 'chat-message__timestamp';
      
      if (timestamp) {
        const date = new Date(timestamp * 1000);
        timestampDiv.textContent = date.toLocaleTimeString();
      } else {
        timestampDiv.textContent = new Date().toLocaleTimeString();
      }
      
      messageDiv.appendChild(senderDiv);
      messageDiv.appendChild(contentDiv);
      messageDiv.appendChild(timestampDiv);
      
      chatContainer.appendChild(messageDiv);
      scrollToBottom();
    }
    
    function addAssistantMessage(message, timestamp = null) {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message chat-message--assistant';
      
      const senderDiv = document.createElement('div');
      senderDiv.className = 'chat-message__sender';
      senderDiv.textContent = 'Assistente IA';
      
      const contentDiv = document.createElement('div');
      contentDiv.className = 'chat-message__content';
      
      // Processar markdown se disponível
      if (typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(message);
      } else {
        contentDiv.textContent = message;
      }
      
      const timestampDiv = document.createElement('div');
      timestampDiv.className = 'chat-message__timestamp';
      
      if (timestamp) {
        const date = new Date(timestamp * 1000);
        timestampDiv.textContent = date.toLocaleTimeString();
      } else {
        timestampDiv.textContent = new Date().toLocaleTimeString();
      }
      
      messageDiv.appendChild(senderDiv);
      messageDiv.appendChild(contentDiv);
      messageDiv.appendChild(timestampDiv);
      
      chatContainer.appendChild(messageDiv);
      scrollToBottom();
    }
    
    function addSystemMessage(message) {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message chat-message--system';
      
      const contentDiv = document.createElement('div');
      contentDiv.className = 'chat-message__content';
      contentDiv.textContent = message;
      
      messageDiv.appendChild(contentDiv);
      chatContainer.appendChild(messageDiv);
      scrollToBottom();
    }
    
    // app/static/js/chat.js (continuação)
  function addLoadingMessage(id) {
    const messageDiv = document.createElement('div');
    messageDiv.id = id;
    messageDiv.className = 'chat-message chat-message--assistant';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-dots';
    loadingDiv.innerHTML = '<span></span><span></span><span></span>';
    
    messageDiv.appendChild(loadingDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
  }
  
  function removeElement(id) {
    const element = document.getElementById(id);
    if (element) {
      element.remove();
    }
  }
  
  function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  
  function startNewConversation() {
    fetch('/new_user', {
      method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        chatContainer.innerHTML = '';
        addSystemMessage('Nova conversa iniciada. Como posso ajudar?');
      } else {
        console.error('Erro ao criar novo usuário:', data.error);
        addSystemMessage('Erro ao iniciar nova conversa. Por favor, tente novamente.');
      }
    })
    .catch(error => {
      console.error('Erro ao criar novo usuário:', error);
      addSystemMessage('Erro ao iniciar nova conversa. Por favor, tente novamente.');
    });
  }
});