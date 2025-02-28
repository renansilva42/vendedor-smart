# app/services/openai_service.py
from openai import OpenAI
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    try:
        return OpenAI(api_key=Config.OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
        return None

client = get_openai_client()