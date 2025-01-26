import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ASSISTANT_ID_VENDAS = os.getenv('ASSISTANT_ID_VENDAS')
    ASSISTANT_ID_TREINAMENTO = os.getenv('ASSISTANT_ID_TREINAMENTO')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    
    print(f"DEBUG: SUPABASE_URL = {SUPABASE_URL}")
    print(f"DEBUG: SUPABASE_KEY = {SUPABASE_KEY[:10]}...")
    print(f"DEBUG: OPENAI_API_KEY = {OPENAI_API_KEY[:10]}...")
    print(f"DEBUG: ASSISTANT_ID_VENDAS = {ASSISTANT_ID_VENDAS}")
    print(f"DEBUG: ASSISTANT_ID_TREINAMENTO = {ASSISTANT_ID_TREINAMENTO}")
    print(f"DEBUG: SECRET_KEY is set: {'Yes' if SECRET_KEY else 'No'}")