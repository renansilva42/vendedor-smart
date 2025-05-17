# app/routes.py (refatorado)
import logging
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.chatbot import ChatbotFactory
from app.models import User, Message, Auth
import uuid
from functools import wraps
from .whatsapp_handler import process_whatsapp_message
from typing import Dict, Any, Callable, Optional
import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criação do blueprint
main = Blueprint('main', __name__)

# Decorator para verificar autenticação
def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("Tentativa de acesso a rota protegida sem autenticação")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas

@main.before_request
def check_session_expiry():
    """Verifica se a sessão expirou."""
    if 'user_id' in session and 'last_activity' in session:
        # Verificar se passaram mais de 30 minutos desde a última atividade
        last_activity = datetime.datetime.fromisoformat(session['last_activity'])
        if (datetime.datetime.now() - last_activity).total_seconds() > 1800:  # 30 minutos
            session.clear()
            return redirect(url_for('main.index'))
    
    # Atualizar timestamp de última atividade
    if 'user_id' in session:
        session['last_activity'] = datetime.datetime.now().isoformat()

@main.route('/')
def index():
    """Rota principal que exibe a página de login ou redireciona para seleção de chatbot."""
    if 'user_id' in session:
        return redirect(url_for('main.select_chatbot'))
    return render_template('index.html')

@main.route('/login', methods=['POST'])
def login():
    """Processa o login do usuário."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            logger.warning("Tentativa de login com dados incompletos")
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'})
        
        # Verificar credenciais
        if Auth.verify_credentials(email, password):
            # Obter ou criar usuário
            user = User.get_or_create_by_email(email)
            
            if not user or 'id' not in user:
                logger.error(f"Falha ao obter ou criar usuário para email: {email}")
                return jsonify({'success': False, 'message': 'Erro ao processar usuário'})
            
            # Verificar se o usuário existe no banco de dados
            user_check = User.get_name(user['id'])
            # Accept "Usuário Anônimo" as valid user name
            if user_check == "Nenhum nome encontrado":
                logger.error(f"Usuário com ID {user['id']} não existe no banco de dados após login")
                return jsonify({'success': False, 'message': 'Usuário inválido ou não encontrado'})
            
            # Configurar sessão
            session['user_id'] = user['id']
            session['email'] = email
            
            logger.info(f"Login bem-sucedido para: {email} com user_id: {user['id']}")
            return jsonify({'success': True})
        else:
            logger.warning(f"Tentativa de login com credenciais inválidas: {email}")
            return jsonify({'success': False, 'message': 'Credenciais inválidas'})
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro no servidor: {str(e)}'})

@main.route('/logout')
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    logger.info("Usuário desconectado")
    return redirect(url_for('main.index'))

@main.route('/select_chatbot')
@login_required
def select_chatbot():
    """Exibe a página de seleção de chatbot."""
    return render_template('select_chatbot.html')

@main.route('/chat/<chatbot_type>')
@login_required
def chat(chatbot_type: str):
    """Inicializa a sessão de chat com o tipo de chatbot especificado."""
    # Verificar se o tipo de chatbot é válido
    if chatbot_type not in ChatbotFactory.get_available_types():
        logger.warning(f"Tentativa de acesso a tipo de chatbot inválido: {chatbot_type}")
        return redirect(url_for('main.select_chatbot'))
    
    user_id = session.get('user_id')
    
    # Obter thread_id existente ou criar novo
    thread_id = User.get_thread_id(user_id, chatbot_type)
    
    if not thread_id:
        # Criar nova thread
        try:
            chatbot = ChatbotFactory.create_chatbot(chatbot_type)
            if not chatbot:
                logger.error(f"Falha ao criar chatbot do tipo: {chatbot_type}")
                return redirect(url_for('main.select_chatbot'))
                
            thread_id = chatbot.create_thread()
            
            # Atualizar thread_id do usuário
            if chatbot_type == 'atual':
                User.update_thread_id_atual(user_id, thread_id)
            elif chatbot_type == 'novo':
                User.update_thread_id_novo(user_id, thread_id)
            elif chatbot_type == 'treinamento':
                User.update_thread_id_treinamento(user_id, thread_id)
            else:
                # Fallback genérico
                User.update_thread_id(user_id, thread_id, chatbot_type)
                
            logger.info(f"Nova thread criada para usuário {user_id}, tipo {chatbot_type}: {thread_id}")
        except Exception as e:
            logger.error(f"Erro ao criar thread: {str(e)}", exc_info=True)
            return redirect(url_for('main.select_chatbot'))
    
    # Atualizar última interação
    User.update_last_interaction(user_id, chatbot_type)
    
    return render_template('chat.html', thread_id=thread_id, chatbot_type=chatbot_type)

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        if not request.is_json:
            return jsonify({'error': 'Requisição deve ser JSON'}), 400

        data = request.json
        message = data.get('message', '').strip()
        chatbot_type = data.get('chatbot_type', 'atual')
        
        if not message:
            return jsonify({'error': 'Mensagem não pode estar vazia'}), 400

        user_id = session.get('user_id')
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # Criar nova thread se não existir
        thread_id = User.get_thread_id(user_id, chatbot_type)
        if not thread_id:
            chatbot = ChatbotFactory.create_chatbot(chatbot_type)
            thread_id = chatbot.create_thread()
            User.update_thread_id(user_id, thread_id, chatbot_type)

        # Obter o nome do usuário - primeiro da tabela de usuários
        # Use o nome armazenado em users mesmo que vazio, pois o chatbot vai pedir na primeira interação
        user_name = user.get('name', '') if user else ''

        # Registrar mensagem do usuário com o nome atual (mesmo que vazio)
        Message.create(
            thread_id=thread_id,
            role="user",
            content=message,
            user_id=user_id,
            chatbot_type=chatbot_type,
            user_name=user_name
        )

        # Obter resposta do chatbot
        chatbot = ChatbotFactory.create_chatbot(chatbot_type)
        response = chatbot.send_message(thread_id, message)

        # Se o chatbot extraiu um nome da mensagem e esse nome não está no banco de dados
        # Vamos atualizar o nome do usuário
        if response and 'user_name' in response and response['user_name'] != user_name and response['user_name'] != "Usuário Anônimo":
            # Atualizar o nome no banco de dados
            updated = User.update_name(user_id, response['user_name'])
            if updated:
                logger.info(f"Nome do usuário atualizado para: {response['user_name']}")

        # Registrar resposta do assistente com nome específico baseado no tipo do chatbot
        if response and 'response' in response:
            assistant_name = "IA Especialista em Vendas"  # Nome padrão
            
            # Usar nome específico para cada tipo de chatbot
            if chatbot_type == 'treinamento' or chatbot_type == 'novo':
                assistant_name = "IA Treinamento de Vendas"
            
            Message.create(
                thread_id=thread_id,
                role="assistant",
                content=response['response'],
                user_id=user_id,
                chatbot_type=chatbot_type,
                user_name=assistant_name
            )

        # Atualizar última interação
        User.update_last_interaction(user_id, chatbot_type)

        response_data = {
            'response': response.get('response', ''),
            'thread_id': thread_id
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main.route('/new_user', methods=['POST'])
@login_required
def new_user():
    """Cria uma nova thread de chatbot para o usuário logado, reiniciando a sessão."""
    try:
        # Validar se a requisição é JSON
        if not request.is_json:
            logger.warning("Requisição não contém JSON válido")
            return jsonify({'error': 'Requisição deve ser JSON'}), 400

        data = request.json
        chatbot_type = data.get('chatbot_type', 'atual')  # Default to 'atual' if not specified
        create_new_thread = data.get('create_new_thread', False)  # Flag para força criação de nova thread
        
        # Validar tipo de chatbot
        if chatbot_type not in ChatbotFactory.get_available_types():
            logger.error(f"Tipo de chatbot inválido: {chatbot_type}")
            return jsonify({'error': 'Tipo de chatbot inválido'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            logger.error("ID do usuário não encontrado na sessão")
            return jsonify({'error': 'Sessão inválida'}), 401
        
        # Verificar se o usuário existe
        user = User.get_by_id(user_id)
        if not user:
            logger.error(f"Usuário não encontrado: {user_id}")
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Criar chatbot e nova thread
        chatbot = ChatbotFactory.create_chatbot(chatbot_type)
        if not chatbot:
            logger.error(f"Falha ao criar chatbot do tipo: {chatbot_type}")
            return jsonify({'error': 'Erro ao criar chatbot'}), 500
        
        # Limpar cache de instâncias para garantir que uma nova instância será criada
        if create_new_thread:
            ChatbotFactory.clear_cache()
            # Invalidar cache do thread_id do usuário
            User.get_thread_id.cache_clear()
            
        thread_id = chatbot.create_thread()
        if not thread_id:
            logger.error("Falha ao criar thread do chatbot")
            return jsonify({'error': 'Erro ao criar thread'}), 500
        
        # Atualizar thread_id do usuário
        update_success = False
        if chatbot_type == 'atual':
            update_success = User.update_thread_id_atual(user_id, thread_id)
        elif chatbot_type == 'novo':
            update_success = User.update_thread_id_novo(user_id, thread_id)
        elif chatbot_type == 'treinamento':
            update_success = User.update_thread_id_treinamento(user_id, thread_id)
        elif chatbot_type == 'vendas':
            # Check if update_thread_id_vendas exists, else fallback to update_thread_id_novo
            if hasattr(User, 'update_thread_id_vendas'):
                update_success = User.update_thread_id_vendas(user_id, thread_id)
            else:
                update_success = User.update_thread_id_novo(user_id, thread_id)
        else:
            # Fallback genérico para outros tipos de chatbot
            update_success = User.update_thread_id(user_id, thread_id, chatbot_type)
        
        if not update_success:
            logger.error(f"Falha ao atualizar thread_id do usuário: {user_id}")
            return jsonify({'error': 'Erro ao atualizar thread_id'}), 500
        
        # Resetar nome do usuário para vazio para prompting de reintrodução
        if User.update_name(user_id, ''):
            logger.info(f"Nome do usuário {user_id} resetado para vazio na nova thread")
            # Limpar mensagens existentes para a nova thread para garantir que não haja histórico
            if create_new_thread:
                # Primeiro criamos a thread, depois limpamos - não podemos limpar mensagens de uma thread que não existe
                Message.clear_thread_history(thread_id)
                logger.info(f"Histórico da thread {thread_id} limpo para garantir nova conversa")
        else:
            logger.warning(f"Falha ao resetar nome do usuário {user_id}")
        
        # Atualizar última interação
        User.update_last_interaction(user_id, chatbot_type)
    
        # Registrar criação bem-sucedida
        logger.info(f"Nova thread criada para usuário {user_id}, tipo {chatbot_type}: {thread_id}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'thread_id': thread_id,
            'chatbot_type': chatbot_type,
            'message': 'Nova sessão iniciada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição de nova thread: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main.route('/get_chat_history')
@login_required
def get_chat_history():
    """Recupera o histórico de chat para o usuário autenticado."""
    try:
        thread_id = request.args.get('thread_id')
        chatbot_type = request.args.get('chatbot_type')
        
        if not thread_id:
            return jsonify({'error': 'ID de thread não especificado'})
        
        messages = Message.get_messages(thread_id, chatbot_type)
        
        return jsonify({'messages': messages})
    except Exception as e:
        logger.error(f"Erro ao recuperar histórico de chat: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)})

@main.route('/dashboard')
@login_required
def dashboard():
    """Exibe o dashboard para o usuário autenticado."""
    return render_template('dashboard.html')

@main.route('/get_dashboard_data')
@login_required
def get_dashboard_data():
    """Recupera dados para o dashboard do usuário."""
    try:
        user_id = session.get('user_id')
        
        # Obter contagem de logins
        login_count = User.get_login_count(user_id)
        
        # Calcular pontuações de conversas
        scores = Message.calculate_conversation_scores(user_id)
        
        # Obter feedback da IA
        ia_feedback = Message.get_ia_feedback(user_id)
        
        # Analisar posicionamento
        posicionamento = Message.analyze_positioning(user_id)
        
        return jsonify({
            'login_count': login_count,
            'scores': scores,
            'ia_feedback': ia_feedback,
            'posicionamento': posicionamento
        })
    except Exception as e:
        logger.error(f"Erro ao obter dados do dashboard: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)})

@main.route('/whatsapp-webhook', methods=['POST', 'GET'])
def whatsapp_webhook():
    """Manipula requisições para o webhook do WhatsApp."""
    if request.method == 'GET':
        # Verificação do webhook
        logger.info("Recebida solicitação GET para webhook do WhatsApp")
        return jsonify({'status': 'ok'})
    
    elif request.method == 'POST':
        try:
            # Processar mensagem recebida
            logger.info("Recebida mensagem POST para webhook do WhatsApp")
            data = request.json
            
            # Processar a mensagem
            result = process_whatsapp_message(data)
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Erro ao processar webhook do WhatsApp: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)})

@main.route('/generate_analysis')
@login_required
def generate_analysis():
    """Gera uma análise resumida das mensagens do WhatsApp."""
    try:
        # Obter mensagens do WhatsApp
        messages = Message.get_whatsapp_messages()
        
        if not messages:
            return jsonify({'summary': 'Não há mensagens para analisar.'})
        
        # Criar chatbot para análise
        chatbot = ChatbotFactory.create_chatbot('whatsapp')
        if not chatbot:
            logger.error("Falha ao criar chatbot do WhatsApp")
            return jsonify({'error': 'Falha ao criar chatbot'})
        
        # Usar o método wrapper que lida com o cache corretamente
        summary = chatbot.summarize_messages(messages)
        
        return jsonify({'summary': summary})
    except Exception as e:
        logger.error(f"Erro ao gerar análise: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)})
