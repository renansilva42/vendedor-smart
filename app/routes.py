import logging
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.chatbot import Chatbot, ChatbotFactory
from app.models import User, Message, Auth
import uuid
from functools import wraps
from .whatsapp_handler import process_whatsapp_message
from app.chatbot import ChatbotFactory

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar o blueprint
main = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    if session.get('authenticated'):
        return redirect(url_for('main.select_chatbot'))
    return render_template('index.html')

@main.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        logger.warning("Tentativa de login sem email ou senha")
        return jsonify({'success': False, 'error': 'Email e senha são obrigatórios'}), 400

    if Auth.verify_credentials(email, password):
        user = User.get_or_create_by_email(email)
        if user and 'error' not in user:
            session['authenticated'] = True
            session['user_id'] = user['id']
            session['user_email'] = email
            session['chatbot_type'] = 'atual'
            logger.info(f"Login bem-sucedido. User ID: {user['id']}, Nome: {user.get('name', 'Não definido')}, Email: {email}, Login Count: {user.get('login_count', 1)}")
            return jsonify({'success': True, 'login_count': user.get('login_count', 1)})
        else:
            logger.error(f"Erro ao obter/criar usuário: {user.get('error')}")
            return jsonify({'success': False, 'error': 'Erro interno'}), 500
    else:
        logger.warning(f"Falha na autenticação para o email: {email}")
        return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

@main.route('/logout')
def logout():
    user_id = session.get('user_id')
    logger.info(f"Usuário deslogado: {user_id}")
    session.clear()
    return redirect(url_for('main.index'))

@main.route('/select_chatbot')
@login_required
def select_chatbot():
    return render_template('select_chatbot.html')

@main.route('/chat/<chatbot_type>')
@login_required
def chat(chatbot_type):
    if chatbot_type not in ['atual', 'novo']:
        return redirect(url_for('main.select_chatbot'))
    
    user_id = session.get('user_id')
    user_name = User.get_name(user_id)
    
    # Usar a fábrica para criar o chatbot
    try:
        chatbot = ChatbotFactory.create_chatbot(chatbot_type)
        thread_id = User.get_thread_id(user_id, chatbot_type) or chatbot.create_thread()
        User.update_thread_id(user_id, thread_id, chatbot_type)
        
        return render_template('chat.html', 
                              chatbot_type=chatbot_type, 
                              thread_id=thread_id,
                              user_name=user_name)
    except Exception as e:
        logger.error(f"Erro ao inicializar chatbot: {str(e)}")
        return redirect(url_for('main.select_chatbot'))

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    message = data.get('message', '')
    thread_id = data.get('thread_id', '')
    chatbot_type = data.get('chatbot_type', '')
    
    if not message or not thread_id or not chatbot_type:
        return jsonify({'error': 'Parâmetros incompletos'}), 400
    
    user_id = session.get('user_id')
    user_name = User.get_name(user_id)
    
    try:
        # Usar a fábrica para criar o chatbot
        chatbot = ChatbotFactory.create_chatbot(chatbot_type)
        
        # Tentar extrair nome da mensagem
        extracted_name = chatbot.extract_name(message)
        if extracted_name and user_name == "Usuário Anônimo":
            success = User.update_name(user_id, extracted_name)
            if success:
                user_name = extracted_name
                # Atualizar nome nas mensagens anteriores
                Message.update_user_name(thread_id, user_id, extracted_name)
                logger.info(f"Nome do usuário atualizado para: {extracted_name}")
        
        # Enviar mensagem
        response = chatbot.send_message(thread_id, message, user_name)
        
        # Tentar atualizar última interação
        try:
            User.update_last_interaction(user_id, chatbot_type)
        except Exception as e:
            logger.warning(f"Erro ao atualizar última interação, mas continuando: {str(e)}")
        
        # Retornar resposta com nome do usuário atualizado
        return jsonify({
            'response': response.get('response', ''),
            'user_name': user_name,
            'error': response.get('error')
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/new_user', methods=['POST'])
@login_required
def new_user():
    try:
        # Obter informações da sessão
        old_user_id = session.get('user_id')
        email = session.get('user_email')
        chatbot_type = session.get('chatbot_type', 'atual')
        
        logger.info(f"Iniciando criação de novo usuário. Usuário anterior: {old_user_id}, Email: {email}, Tipo: {chatbot_type}")

        # Criar novo usuário
        new_user_id = str(uuid.uuid4())
        new_user = User.create(new_user_id, name="Usuário Anônimo", email=email)
        
        if not new_user:
            raise Exception("Falha ao criar novo usuário no banco de dados")

        # Criar nova thread usando a fábrica de chatbot
        try:
            chatbot = ChatbotFactory.create_chatbot(chatbot_type)
            new_thread_id = chatbot.create_thread()
            
            if not new_thread_id:
                raise Exception("Falha ao criar nova thread no chatbot")
                
            logger.info(f"Nova thread criada: {new_thread_id}")
            
            # Atualizar thread_id no usuário
            success = User.update_thread_id(new_user_id, new_thread_id, chatbot_type)
            if not success:
                raise Exception("Falha ao atualizar thread_id no usuário")
                
            # Atualizar sessão
            session['user_id'] = new_user_id
            
            logger.info(f"Novo usuário criado com sucesso. ID: {new_user_id}, Thread: {new_thread_id}")
            
            return jsonify({
                'success': True,
                'thread_id': new_thread_id,
                'user_id': new_user_id,
                'message': 'Novo usuário criado com sucesso'
            })
            
        except Exception as e:
            logger.error(f"Erro ao criar thread: {str(e)}")
            # Limpar o usuário criado em caso de falha
            User.delete(new_user_id)
            raise Exception(f"Erro ao criar thread: {str(e)}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao criar novo usuário: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@main.route('/get_chat_history')
@login_required
def get_chat_history():
    user_id = session.get('user_id')
    chatbot_type = session.get('chatbot_type')
    if not user_id or not chatbot_type:
        logger.warning("Tentativa de obter histórico de chat sem user_id ou chatbot_type")
        return jsonify([])

    thread_id = User.get_thread_id(user_id, chatbot_type)
    if not thread_id:
        logger.warning(f"Nenhuma thread encontrada para user_id: {user_id}, chatbot_type: {chatbot_type}")
        return jsonify([])

    messages = Message.get_messages(thread_id, chatbot_type)
    logger.info(f"Histórico de chat obtido para thread_id: {thread_id}")
    return jsonify(messages)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/get_dashboard_data')
@login_required
def get_dashboard_data():
    user_id = session.get('user_id')
    
    login_count = User.get_login_count(user_id)
    scores = Message.calculate_conversation_scores(user_id)
    ia_feedback = Message.get_ia_feedback(user_id)
    posicionamento = Message.analyze_positioning(user_id)
    
    if isinstance(scores, dict):
        data = {
            'login_count': login_count,
            'lead_score': scores.get('lead_score', 0),
            'ia_conversation_score': scores.get('ia_conversation_score', 0),
            'ia_evaluation_score': scores.get('ia_evaluation_score', 0),
            'ia_feedback': ia_feedback,
            'posicionamento': posicionamento
        }
    else:
        data = {'error': 'Dados não disponíveis'}
    
    logger.info(f"Dados do dashboard obtidos para user_id: {user_id}")
    return jsonify(data)

@main.route('/whatsapp-webhook', methods=['POST', 'GET'])
def whatsapp_webhook():
    logger.info("Webhook do WhatsApp acionado")
    logger.debug(f"Método da requisição: {request.method}")
    logger.debug(f"Headers: {request.headers}")

    if request.method == 'GET':
        logger.info("Requisição GET recebida no webhook do WhatsApp")
        return jsonify({
            "status": "active",
            "message": "Este é o endpoint do webhook do WhatsApp. Use POST para enviar dados."
        }), 200

    elif request.method == 'POST':
        logger.info("Requisição POST recebida no webhook do WhatsApp")
        try:
            message_data = request.json
            logger.debug(f"Dados recebidos: {message_data}")

            if not message_data:
                logger.warning("Nenhum dado fornecido na requisição POST")
                return jsonify({"status": "error", "message": "Dados não fornecidos"}), 400

            if 'messages' not in message_data:
                logger.warning("Estrutura de dados inválida")
                return jsonify({"status": "error", "message": "Formato de mensagem inválido"}), 400

            processed_data = {
                'sender': message_data.get('from'),
                'content': message_data.get('text', {}).get('body'),
                'timestamp': message_data.get('timestamp')
            }

            logger.info("Processando mensagem do WhatsApp")
            result = process_whatsapp_message(processed_data)
            logger.info(f"Resultado do processamento: {result}")
            
            return jsonify({"status": "success", "result": result}), 200

        except Exception as e:
            logger.error(f"Erro no webhook do WhatsApp: {e}", exc_info=True)
            return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

    else:
        logger.warning(f"Método não permitido: {request.method}")
        return jsonify({"status": "error", "message": "Método não permitido"}), 405

@main.route('/generate_analysis')
@login_required
def generate_analysis():
    logger.info("Iniciando geração de análise")
    try:
        messages = Message.get_whatsapp_messages()
        logger.info(f"Obtidas {len(messages)} mensagens do WhatsApp")
        
        chatbot = Chatbot('whatsapp')
        summary = chatbot.generate_summary(messages)
        logger.info("Resumo gerado com sucesso")
        
        if isinstance(summary, dict):
            formatted_summary = summary.get('response', '')
        else:
            formatted_summary = summary
        
        formatted_summary = f"""
        <div class="analysis-summary">
            <h2>Análise de Mensagens do WhatsApp</h2>
            {formatted_summary}
        </div>
        """
        
        return jsonify({'summary': formatted_summary})
    except Exception as e:
        logger.error(f"Erro ao gerar análise: {e}", exc_info=True)
        return jsonify({'error': 'Erro ao gerar análise'}), 500