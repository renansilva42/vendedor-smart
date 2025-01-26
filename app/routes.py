from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.chatbot import Chatbot
from app.models import User, Message, Auth
import uuid
from functools import wraps

bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
def index():
    if session.get('authenticated'):
        return redirect(url_for('main.select_chatbot'))
    return render_template('index.html')

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email e senha são obrigatórios'}), 400

    if Auth.verify_credentials(email, password):
        session['authenticated'] = True
        user = User.get_or_create_by_email(email)
        session['user_id'] = user['id']
        session['user_email'] = email
        session['chatbot_type'] = 'atual'
        print(f"Login bem-sucedido. User ID: {user['id']}, Nome: {user.get('name', 'Não definido')}, Email: {email}, Login Count: {user.get('login_count', 1)}")
        return jsonify({'success': True, 'login_count': user.get('login_count', 1)})
    else:
        print(f"Falha na autenticação para o email: {email}")
        return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401

@bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    print(f"Usuário deslogado: {user_id}")
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/select_chatbot')
@login_required
def select_chatbot():
    return render_template('select_chatbot.html')

@bp.route('/chat/<chatbot_type>')
@login_required
def chat(chatbot_type):
    session['chatbot_type'] = chatbot_type
    user_id = session.get('user_id')
    print(f"Iniciando chat para usuário {user_id} com chatbot tipo: {chatbot_type}")
    return render_template('chat.html', chatbot_type=chatbot_type)

@bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    print("Iniciando send_message")
    data = request.json
    message = data['message']
    chatbot_type = data.get('chatbot_type')
    user_id = session.get('user_id')
    print(f"User ID: {user_id}, Chatbot Type: {chatbot_type}, Mensagem: '{message}'")

    if not user_id or not chatbot_type:
        return jsonify({'error': 'Usuário não autenticado ou tipo de chatbot não especificado'}), 400

    chatbot = Chatbot(chatbot_type)

    thread_id = User.get_thread_id(user_id, chatbot_type)
    if not thread_id:
        thread_id = chatbot.create_thread()
        User.update_thread_id(user_id, thread_id, chatbot_type)
        print(f"Nova thread criada: {thread_id} para usuário {user_id} e chatbot {chatbot_type}")
    else:
        User.update_last_interaction(user_id, chatbot_type)
        print(f"Thread existente atualizada: {thread_id} para usuário {user_id} e chatbot {chatbot_type}")

    current_user_name = User.get_name(user_id)
    print(f"Nome atual do usuário: {current_user_name}")

    if current_user_name in ["Usuário Anônimo", "Nenhum nome encontrado"]:
        extracted_name = chatbot.extract_name(message)
        print(f"Nome extraído pelo chatbot: {extracted_name}")
        if extracted_name and extracted_name.lower() != "nenhum nome encontrado":
            try:
                print(f"Tentando atualizar nome do usuário {user_id} para: {extracted_name}")
                updated_user = User.update_name(user_id, extracted_name)
                if updated_user:
                    print(f"Nome do usuário atualizado para: {extracted_name}")
                    current_user_name = extracted_name
                    # Atualizar mensagens anteriores com o novo nome
                    Message.update_user_name(thread_id, user_id, current_user_name)
                else:
                    print("Falha ao atualizar o nome do usuário no Supabase")
            except Exception as e:
                print(f"Erro ao atualizar nome do usuário: {e}")
    else:
        print(f"Nome do usuário já definido: {current_user_name}")

    user_message = Message.create(thread_id, 'user', message, user_id, chatbot_type, current_user_name)
    if user_message:
        print(f"Mensagem do usuário criada: {user_message}")
    else:
        print("Falha ao criar mensagem do usuário")

    response = chatbot.send_message(thread_id, message)
    
    assistant_message = Message.create(thread_id, 'assistant', response, None, chatbot_type, 'Assistente IA')
    if assistant_message:
        print(f"Mensagem do assistente criada: {assistant_message}")
    else:
        print("Falha ao criar mensagem do assistente")

    return jsonify({'response': response})

@bp.route('/new_user', methods=['POST'])
@login_required
def new_user():
    old_user_id = session.pop('user_id', None)
    session.pop('user_name', None)
    chatbot_type = session.pop('chatbot_type', None)
    email = session.get('user_email')  # Adicione esta linha para obter o email da sessão
    print(f"Iniciando nova conversa. Usuário anterior: {old_user_id}")

    new_user_id = str(uuid.uuid4())
    new_user = User.create(new_user_id, name="Usuário Anônimo", email=email)
    if new_user:
        session['user_id'] = new_user_id
        session['chatbot_type'] = chatbot_type
        print(f"Novo user_id gerado e salvo: {new_user_id}, Chatbot Type: {chatbot_type}, Email: {email}")
    else:
        print("Falha ao criar novo usuário")
        return jsonify({'success': False, 'error': 'Falha ao criar novo usuário'}), 500

    return jsonify({'success': True})

@bp.route('/get_chat_history')
@login_required
def get_chat_history():
    user_id = session.get('user_id')
    chatbot_type = session.get('chatbot_type')
    if not user_id or not chatbot_type:
        return jsonify([])

    thread_id = User.get_thread_id(user_id, chatbot_type)
    if not thread_id:
        return jsonify([])

    messages = Message.get_messages(thread_id, chatbot_type)
    return jsonify(messages)