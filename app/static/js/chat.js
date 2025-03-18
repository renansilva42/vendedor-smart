// app/static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
  const chatContainer = document.querySelector('.chat-container');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const backBtn = document.getElementById('back-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const newUserBtn = document.getElementById('new-user-btn');

  // Verificar se os elementos foram encontrados e logar no console
  if (!chatContainer) console.error('Chat container não encontrado');
  if (!userInput) console.error('Input não encontrado');
  if (!sendBtn) console.error('Botão enviar não encontrado');
  if (!backBtn) console.error('Botão voltar não encontrado');
  if (!logoutBtn) console.error('Botão logout não encontrado');
  if (!newUserBtn) console.error('Botão novo usuário não encontrado');
  
  let isProcessing = false;
  let userName = 'Usuário';
  
  // Obter thread_id do elemento data
  let threadId = chatContainer ? chatContainer.dataset.threadId : null;
  const chatbotType = chatContainer ? chatContainer.dataset.chatbotType : null;
  
  // Event listeners com logs
  if (sendBtn) {
      sendBtn.addEventListener('click', function() {
          console.log('Botão enviar clicado');
          sendMessage();
      });
  }

  if (backBtn) {
      backBtn.addEventListener('click', function() {
          console.log('Botão voltar clicado');
          window.location.href = '/select_chatbot';
      });
  }

  if (logoutBtn) {
      logoutBtn.addEventListener('click', function() {
          console.log('Botão logout clicado');
          window.location.href = '/logout';
      });
  }

  if (newUserBtn) {
      newUserBtn.addEventListener('click', function() {
          console.log('Botão novo usuário clicado');
          if (confirm('Iniciar uma nova conversa? O histórico atual será mantido, mas você começará com um novo usuário.')) {
              startNewConversation();
          }
      });
  }

  if (userInput) {
      userInput.addEventListener('keypress', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
          }
      });
  }

  // Carregar histórico de chat apenas se o container existir
  if (chatContainer) {
      loadChatHistory();
  }
    
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
  
      const currentThreadId = document.getElementById('chat-container').dataset.threadId;
  
      addUserMessage(message);
      userInput.value = '';
  
      const loadingId = 'loading-' + Date.now();
      addLoadingMessage(loadingId);
  
      fetch('/send_message', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({
              message: message,
              thread_id: currentThreadId,
              chatbot_type: chatbotType
          }),
      })
      .then(response => response.json())
      .then(data => {
          removeElement(loadingId);
  
          if (data.error) {
              addSystemMessage('Erro: ' + data.error);
              return;
          }
  
          if (data.user_name && data.user_name !== userName) {
              userName = data.user_name;
              document.querySelectorAll('.chat-message--user .chat-message__sender').forEach(el => {
                  el.textContent = userName;
              });
          }
  
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
    // Mostrar indicador de carregamento
    const loadingId = 'loading-new-user';
    addLoadingMessage(loadingId);

    fetch('/new_user', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro na resposta do servidor');
      }
      return response.json();
    })
    .then(data => {
      removeElement(loadingId);
      
      if (data.success && data.thread_id) {
        // Atualizar thread_id no DOM
        document.getElementById('chat-container').dataset.threadId = data.thread_id;
        threadId = data.thread_id;
        
        // Limpar chat e adicionar mensagem inicial
        chatContainer.innerHTML = '';
        userName = 'Usuário Anônimo';
        addSystemMessage('Olá! Por favor, me diga seu nome para começarmos nossa conversa.');
        
        // Reabilitar input e botão
        userInput.disabled = false;
        sendBtn.disabled = false;
        
        // Enviar mensagem automática para o backend
        fetch('/send_message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: "Olá! Sou seu assistente virtual. Por favor, me diga seu nome para que eu possa te atender melhor.",
            thread_id: data.thread_id,
            chatbot_type: chatbotType
          }),
        });
      } else {
        throw new Error(data.error || 'Erro desconhecido ao criar novo usuário');
      }
    })
    .catch(error => {
      console.error('Erro ao criar novo usuário:', error);
      removeElement(loadingId);
      addSystemMessage('Erro ao iniciar nova conversa: ' + error.message);
    });
  }
});

// Event listeners com logs
sendBtn.addEventListener('click', function() {
  console.log('Botão enviar clicado');
  sendMessage();
});

backBtn.addEventListener('click', function() {
  console.log('Botão voltar clicado');
  window.location.href = '/select_chatbot';
});

logoutBtn.addEventListener('click', function() {
  console.log('Botão logout clicado');
  window.location.href = '/logout';
});

newUserBtn.addEventListener('click', function() {
  console.log('Botão novo usuário clicado');
  if (confirm('Iniciar uma nova conversa? O histórico atual será mantido, mas você começará com um novo usuário.')) {
      startNewConversation();
  }
});