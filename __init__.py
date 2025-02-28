# app/__init__.py (refatorado)
from flask import Flask
from flask_cors import CORS
from config import Config
import logging
from flask_caching import Cache

# Configuração de logging
logger = logging.getLogger(__name__)

# Inicialização do cache
cache = Cache()

def create_app():
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    
    # Configurar CORS
    CORS(app)
    
    # Carregar configurações
    app.config.from_object(Config)
    
    # Configurar cache
    cache.init_app(app)
    
    # Configurar sessão
    app.secret_key = Config.SECRET_KEY
    
    # Registrar blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Configurar manipuladores de erro
    @app.errorhandler(404)
    def page_not_found(e):
        return "Página não encontrada", 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Erro interno do servidor: {str(e)}")
        return "Erro interno do servidor", 500
    
    # Log de inicialização
    logger.info("Aplicação Flask inicializada com sucesso")
    
    return app