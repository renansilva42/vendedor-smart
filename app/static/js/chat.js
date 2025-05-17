// app/static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    // Seleção dos elementos
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const backBtn = document.getElementById('back-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const newUserBtn = document.getElementById('new-user-btn');

    // Verificação de elementos com logs de depuração
    if (!chatContainer) console.error('Chat container não encontrado');
    if (!userInput) console.error('Input não encontrado');
    if (!sendBtn) console.error('Botão enviar não encontrado');
    if (!backBtn) console.error('Botão voltar não encontrado');
    if (!logoutBtn) console.error('Botão logout não encontrado');
    if (!newUserBtn) console.error('Botão novo usuário não encontrado');

    // Variáveis globais
    let isProcessing = false;
    let userName = 'Você';
    let threadId = chatContainer ? chatContainer.dataset.threadId : null;
    const chatbotType = chatContainer ? chatContainer.dataset.chatbotType : null;

    // Event Listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', function() {
            console.log('Botão enviar clicado');
            sendMessage();
        });
    }

    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter pressionado');
                sendMessage();
            }
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
            if (confirm('Iniciar uma nova conversa? O histórico atual será mantido no servidor, mas você começará com um novo usuário.')) {
                startNewConversation();
            }
        });
    }

    // Carregar histórico de chat se o container existir
    if (chatContainer) {
        loadChatHistory();
    }

    // Funções
    function loadChatHistory() {
        // Verificar se existe um threadId salvo no localStorage
        const savedThreadId = localStorage.getItem('lastThreadId');
        
        // Se houver um threadId salvo e não houver um threadId definido no DOM, usar o salvo
        if (savedThreadId && (!threadId || threadId === 'null')) {
            threadId = savedThreadId;
            // Atualizar o threadId no DOM
            if (chatContainer) {
                chatContainer.dataset.threadId = threadId;
            }
        }
        
        // Construir a URL para buscar o histórico, incluindo o threadId se disponível
        let url = '/get_chat_history';
        if (threadId && threadId !== 'null') {
            url += `?thread_id=${threadId}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.thread_id) {
                    // Atualizar o threadId no DOM e na variável local
                    threadId = data.thread_id;
                    if (chatContainer) {
                        chatContainer.dataset.threadId = threadId;
                    }
                    // Salvar o threadId no localStorage para uso futuro
                    localStorage.setItem('lastThreadId', threadId);
                }
                
                if (data.messages && data.messages.length > 0) {
                    chatContainer.innerHTML = '';
                    data.messages.forEach(msg => {
                        if (msg.role === 'user') {
                            addUserMessage(msg.content, msg.timestamp, msg.user_name);
                            if (msg.user_name && msg.user_name !== 'Usuário Anônimo') {
                                userName = 'Você';
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

        // Obter o thread_id atual do DOM
        const currentThreadId = document.getElementById('chat-container').dataset.threadId;
        
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
                thread_id: currentThreadId,
                chatbot_type: chatbotType
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remover indicador de carregamento
            removeElement(loadingId);
            
            if (data.error) {
                addSystemMessage('Erro: ' + data.error);
                return;
            }
            
            // Atualizar nome do usuário se necessário
            if (data.user_name && data.user_name !== userName) {
                userName = 'Você';
                // Atualizar nome em mensagens anteriores
                document.querySelectorAll('.chat-message--user .chat-message__sender').forEach(el => {
                    el.textContent = 'Você';
                });
            }
            
            // Se houver um thread_id na resposta, atualizar e salvar
            if (data.thread_id) {
                threadId = data.thread_id;
                document.getElementById('chat-container').dataset.threadId = threadId;
                localStorage.setItem('lastThreadId', threadId);
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
        senderDiv.textContent = 'Você';
        
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
        senderDiv.textContent = 'IA Especialista em Vendas';
        
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
            },
            body: JSON.stringify({
                chatbot_type: chatbotType,
                create_new_thread: true  // Adicionar flag para indicar que desejamos uma nova thread
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na resposta do servidor: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            removeElement(loadingId);
            
            if (data.success && data.thread_id) {
                console.log(`Nova thread criada com ID: ${data.thread_id}`);
                
                // Primeiro remover o threadId antigo do localStorage
                localStorage.removeItem('lastThreadId');
                
                // Atualizar thread_id no DOM e variável local
                document.getElementById('chat-container').dataset.threadId = data.thread_id;
                threadId = data.thread_id;
                
                // Salvar o novo threadId no localStorage
                localStorage.setItem('lastThreadId', threadId);
                
                // Limpar chat e adicionar mensagem inicial
                chatContainer.innerHTML = '';
                userName = 'Você';
                addSystemMessage(data.message || 'Nova conversa iniciada! Como posso ajudar?');
                
                // Reabilitar input e botão
                userInput.disabled = false;
                sendBtn.disabled = false;
            } else {
                throw new Error(data.error || 'Erro desconhecido ao criar nova thread');
            }
        })
        .catch(error => {
            console.error('Erro ao criar nova thread:', error);
            removeElement(loadingId);
            addSystemMessage(`Erro ao iniciar nova conversa: ${error.message}`);
        });
    }
});
