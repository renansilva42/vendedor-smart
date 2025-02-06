function displayMessage(sender, message) {
    const chatContainer = document.getElementById('chat-container');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender.toLowerCase()}-message`;

    // Converta o texto Markdown para HTML
    const html = marked.parse(message);

    // Exiba o HTML no navegador
    messageElement.innerHTML = `<strong>${sender}:</strong> ${html}`;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    userInput.value = '';

    if (message === '') return;

    displayMessage('Você', message);
    showTypingIndicator();

    axios.post('/send_message', { 
        message: message,
        chatbot_type: chatbotType
    })
    .then(response => {
        hideTypingIndicator();
        displayMessage('IA', response.data.response);
    })
    .catch(error => {
        hideTypingIndicator();
        console.error('Erro:', error);
        displayMessage('Erro', 'Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.');
    });
}

function showTypingIndicator() {
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.createElement('div');
    typingIndicator.id = 'typing-indicator';
    typingIndicator.className = 'message ia-message';
    typingIndicator.innerHTML = 'IA está digitando...';
    chatContainer.appendChild(typingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function newUser() {
    axios.post('/new_user')
        .then(() => {
            document.getElementById('chat-container').innerHTML = '';
            displayMessage('Sistema', 'Nova conversa iniciada.');
        })
        .catch(error => {
            console.error('Erro:', error);
            displayMessage('Erro', 'Ocorreu um erro ao criar um novo usuário. Por favor, tente novamente.');
        });
}

function logout() {
    axios.get('/logout')
        .then(() => {
            window.location.href = "/";
        })
        .catch(error => {
            console.error('Erro ao fazer logout:', error);
            alert('Erro ao fazer logout. Por favor, tente novamente.');
        });
}

function goBack() {
    window.location.href = "/select_chatbot";
}

function loadChatHistory(chatbotType) {
    axios.get('/get_chat_history', {
        params: { chatbot_type: chatbotType }
    })
    .then(response => {
        const messages = response.data;
        messages.forEach(msg => {
            displayMessage(msg.role === 'user' ? 'Você' : 'IA', msg.content);
        });
    })
    .catch(error => {
        console.error('Erro ao carregar histórico:', error);
        displayMessage('Erro', 'Não foi possível carregar o histórico de mensagens.');
    });
}

function setupEventListeners() {
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('back-btn').addEventListener('click', goBack);
    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('new-user-btn').addEventListener('click', newUser);
}

function initChat(chatbotType) {
    loadChatHistory(chatbotType);
    setupEventListeners();
}

window.onload = function() {
    initChat(chatbotType);
};