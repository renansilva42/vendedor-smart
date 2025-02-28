# app/whatsapp_handler.py (refatorado)
import logging
from app.models import supabase
import datetime
import json
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

def process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma mensagem recebida do WhatsApp e armazena no banco de dados.
    
    Args:
        message_data: Dicionário contendo os dados da mensagem
        
    Returns:
        Dicionário com o resultado do processamento
    """
    try:
        logger.info(f"Processando mensagem do WhatsApp: {message_data}")
        
        # Validar dados da mensagem
        if not message_data:
            logger.warning("Dados de mensagem vazios")
            return {"status": "error", "message": "Dados vazios"}
        
        # Extrair informações relevantes
        sender = message_data.get('sender', 'Desconhecido')
        content = message_data.get('content', '')
        timestamp = message_data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Validar conteúdo
        if not content or not isinstance(content, str):
            logger.warning(f"Conteúdo de mensagem inválido: {content}")
            return {"status": "error", "message": "Conteúdo inválido"}
        
        # Limitar tamanho do conteúdo
        if len(content) > 10000:
            content = content[:10000] + "... (truncado)"
            logger.warning("Conteúdo da mensagem truncado por exceder 10000 caracteres")
        
        # Preparar dados para armazenamento
        message_record = {
            "sender_name": sender,
            "content": content,
            "timestamp": timestamp,
            "processed_at": datetime.datetime.now().isoformat()
        }
        
        # Armazenar no banco de dados
        result = supabase.table('whatsapp_messages').insert(message_record).execute()
        
        if not result.data:
            logger.error("Falha ao inserir mensagem no banco de dados")
            return {"status": "error", "message": "Falha ao armazenar mensagem"}
        
        logger.info(f"Mensagem do WhatsApp processada com sucesso: ID {result.data[0].get('id')}")
        
        return {
            "status": "success",
            "message": "Mensagem processada com sucesso",
            "record_id": result.data[0].get('id')
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem do WhatsApp: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Erro interno: {str(e)}"}