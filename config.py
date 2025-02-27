import os
from dotenv import load_dotenv
import sys

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ASSISTANT_ID_VENDAS = os.getenv('ASSISTANT_ID_VENDAS')
    ASSISTANT_ID_TREINAMENTO = os.getenv('ASSISTANT_ID_TREINAMENTO')
    ASSISTANT_ID_WHATSAPP = os.getenv('ASSISTANT_ID_WHATSAPP')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    WHATSAPP_WEBHOOK_TOKEN = os.getenv('WHATSAPP_WEBHOOK_TOKEN')
    
    # Adicione estas linhas para configurar o SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Seus prints de debug (você pode manter ou remover conforme necessário)
    print(f"DEBUG: SUPABASE_URL = {SUPABASE_URL}")
    print(f"DEBUG: SUPABASE_KEY = {SUPABASE_KEY[:10] if SUPABASE_KEY else 'Not set'}...")
    print(f"DEBUG: OPENAI_API_KEY = {OPENAI_API_KEY[:10] if OPENAI_API_KEY else 'Not set'}...")
    print(f"DEBUG: ASSISTANT_ID_VENDAS = {ASSISTANT_ID_VENDAS}")
    print(f"DEBUG: ASSISTANT_ID_TREINAMENTO = {ASSISTANT_ID_TREINAMENTO}")
    print(f"DEBUG: SECRET_KEY is set: {'Yes' if SECRET_KEY else 'No'}")
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {SQLALCHEMY_DATABASE_URI}")
    print(f"DEBUG: ASSISTANT_ID_WHATSAPP = {ASSISTANT_ID_WHATSAPP}")

# Validar variáveis críticas
    @classmethod
    def validate_config(cls):
        missing_vars = []
        for var in ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY']:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"ERRO: As seguintes variáveis de ambiente são obrigatórias: {', '.join(missing_vars)}")
            sys.exit(1)