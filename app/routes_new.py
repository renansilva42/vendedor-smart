from flask import (
    render_template, redirect, url_for, request,
    jsonify, session, flash, current_app, make_response
)
from functools import wraps
import logging
from .services.container import get_container
from .chatbot.factory import create_chatbot
from .services.interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    LoggingServiceInterface
)

logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator to check if user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def add_cache_headers(response):
    """Add cache control headers to response."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def init_routes(app):
    """Initialize routes for the application."""
    
    container = get_container()
    db_service = container.get(DatabaseServiceInterface)
    logger_service = container.get(LoggingServiceInterface)

    @app.after_request
    def after_request(response):
        """Add headers after each request."""
        return add_cache_headers(response)

    @app.route('/')
    def index():
        """Landing page route."""
        if 'user_id' in session:
            return redirect(url_for('select_chatbot'))
        return render_template('index_new.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route."""
        if request.method == 'POST':
            try:
                # Implement your login logic here
                session['user_id'] = 'demo_user'
                session['theme'] = request.form.get('theme', 'light')
                
                response = make_response(jsonify({
                    'status': 'success',
                    'redirect': url_for('select_chatbot')
                }))
                return response
            except Exception as e:
                logger_service.error(f"Login error: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': 'Erro ao fazer login. Tente novamente.'
                }), 400
        
        return render_template('index_new.html')

    @app.route('/logout', methods=['POST'])
    def logout():
        """Logout route."""
        session.clear()
        return jsonify({'status': 'success', 'redirect': url_for('index')})

    @app.route('/select_chatbot')
    @login_required
    def select_chatbot():
        """Chatbot selection page route."""
        try:
            # Get user preferences from database
            user_id = session.get('user_id')
            user_prefs = db_service.get_user_preferences(user_id) if user_id else {}
            
            return render_template('select_chatbot_new.html',
                user_preferences=user_prefs,
                theme=session.get('theme', 'light')
            )
        except Exception as e:
            logger_service.error(f"Error loading chatbot selection: {str(e)}", exc_info=True)
            flash('Erro ao carregar seleção de chatbot.', 'error')
            return redirect(url_for('index'))

    @app.route('/chat/<chatbot_type>')
    @login_required
    def chat(chatbot_type):
        """Chat interface route."""
        try:
            # Validate chatbot type
            valid_types = ['vendas', 'treinamento']
            if chatbot_type not in valid_types:
                raise ValueError(f"Invalid chatbot type: {chatbot_type}")
            
            # Create or get existing thread
            thread_id = request.args.get('thread_id')
            if not thread_id:
                chatbot = create_chatbot(chatbot_type)
                thread_id = chatbot.create_thread()
            
            # Get chat history
            history = db_service.get_chat_history(thread_id, limit=50)
            
            return render_template('chat_new.html',
                thread_id=thread_id,
                chatbot_type=chatbot_type,
                chat_history=history,
                theme=session.get('theme', 'light')
            )
            
        except ValueError as e:
            logger_service.warning(f"Invalid chatbot type requested: {str(e)}")
            flash('Tipo de chatbot inválido.', 'error')
            return redirect(url_for('select_chatbot'))
        except Exception as e:
            logger_service.error(f"Error initializing chat: {str(e)}", exc_info=True)
            flash('Erro ao iniciar chat. Tente novamente.', 'error')
            return redirect(url_for('select_chatbot'))

    @app.route('/api/send_message', methods=['POST'])
    @login_required
    def send_message():
        """API endpoint for sending messages."""
        try:
            data = request.json
            message = data.get('message')
            thread_id = data.get('thread_id')
            chatbot_type = data.get('chatbot_type')
            
            if not all([message, thread_id, chatbot_type]):
                raise ValueError("Missing required parameters")
            
            # Get chatbot instance
            chatbot = create_chatbot(chatbot_type)
            
            # Process message
            response = chatbot.process_message(
                thread_id=thread_id,
                message=message,
                user_name=session.get('user_id', 'anonymous')
            )
            
            return jsonify(response)
            
        except ValueError as e:
            logger_service.warning(f"Invalid message request: {str(e)}")
            return jsonify({
                'error': 'Parâmetros inválidos',
                'details': str(e)
            }), 400
        except Exception as e:
            logger_service.error(f"Error processing message: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Erro ao processar mensagem',
                'details': str(e)
            }), 500

    @app.route('/api/chat_history')
    @login_required
    def get_chat_history():
        """API endpoint for retrieving chat history."""
        try:
            thread_id = request.args.get('thread_id')
            limit = request.args.get('limit', 50, type=int)
            
            if not thread_id:
                raise ValueError("Thread ID is required")
            
            history = db_service.get_chat_history(thread_id, limit=limit)
            return jsonify({'history': history})
            
        except ValueError as e:
            logger_service.warning(f"Invalid history request: {str(e)}")
            return jsonify({
                'error': 'Parâmetros inválidos',
                'details': str(e)
            }), 400
        except Exception as e:
            logger_service.error(f"Error fetching chat history: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Erro ao buscar histórico',
                'details': str(e)
            }), 500

    @app.route('/api/save_preference', methods=['POST'])
    @login_required
    def save_preference():
        """API endpoint for saving user preferences."""
        try:
            data = request.json
            preference_type = data.get('type')
            value = data.get('value')
            
            if not all([preference_type, value]):
                raise ValueError("Missing required parameters")
            
            user_id = session.get('user_id')
            if preference_type == 'theme':
                session['theme'] = value
            
            db_service.save_user_preference(user_id, preference_type, value)
            return jsonify({'status': 'success'})
            
        except Exception as e:
            logger_service.error(f"Error saving preference: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Erro ao salvar preferência',
                'details': str(e)
            }), 500

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html',
            theme=session.get('theme', 'light')
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger_service.error(f"Internal server error: {str(error)}", exc_info=True)
        return render_template('errors/500.html',
            theme=session.get('theme', 'light')
        ), 500

    return app
