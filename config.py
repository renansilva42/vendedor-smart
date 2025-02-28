# config.py (refatorado)
import os
from dotenv import load_dotenv
import sys
import logging

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Classe de configuração centralizada para a aplicação."""
    
    # Configurações do Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Configurações da OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # IDs dos assistentes
    ASSISTANT_ID_VENDAS = os.getenv('ASSISTANT_ID_VENDAS')
    ASSISTANT_ID_TREINAMENTO = os.getenv('ASSISTANT_ID_TREINAMENTO')
    ASSISTANT_ID_WHATSAPP = os.getenv('ASSISTANT_ID_WHATSAPP')
    
    # Configurações do Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'chave-secreta-padrao')
    
    # Configurações do WhatsApp
    WHATSAPP_WEBHOOK_TOKEN = os.getenv('WHATSAPP_WEBHOOK_TOKEN')
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de cache
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Configurações de timeout
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    
    @classmethod
    def validate_config(cls):
        """Verifica se todas as variáveis de ambiente necessárias estão definidas."""
        missing_vars = []
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY']
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Variáveis de ambiente obrigatórias não definidas: {', '.join(missing_vars)}")
            logger.error("Por favor, defina estas variáveis no arquivo .env ou nas variáveis de ambiente do sistema.")
            sys.exit(1)
        
        logger.info("Configuração validada com sucesso!")

# Validar configuração ao importar o módulo
Config.validate_config()