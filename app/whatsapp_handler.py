import logging
from supabase import create_client
from config import Config
from datetime import datetime, timezone

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    logger.info("Conexão com Supabase estabelecida com sucesso")
except Exception as e:
    logger.error(f"Erro ao conectar com Supabase: {e}", exc_info=True)

def process_whatsapp_message(message_data):
    logger.info("Iniciando processamento da mensagem do WhatsApp")
    try:
        logger.debug(f"Dados da mensagem: {message_data}")
        
        # Extrair informações do remetente e destinatário
        sender_number = message_data.get('data', {}).get('key', {}).get('remoteJid', 'Desconhecido')
        receiver = message_data.get('instance', 'Desconhecido')
        is_from_me = message_data.get('data', {}).get('key', {}).get('fromMe', False)

        # Obter o nome do contato, se disponível
        sender_name = message_data.get('data', {}).get('pushName')
        
        # Se a mensagem for enviada pelo webhook, trocar sender e receiver
        if is_from_me:
            sender_number, receiver = receiver, sender_number
            sender_name = "Webhook"  # ou o nome que você quiser dar ao seu sistema

        message_content = message_data.get('data', {}).get('message', {}).get('conversation', '')
        
        timestamp = message_data.get('date_time')
        try:
            if timestamp:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                raise ValueError("Timestamp não fornecido")
        except (ValueError, AttributeError):
            timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Mensagem de {sender_name or sender_number} para {receiver}")
        logger.debug(f"Conteúdo da mensagem: {message_content}")
        logger.debug(f"Timestamp: {timestamp}")

        whatsapp_message = {
            'sender_number': sender_number,
            'sender_name': sender_name,
            'receiver': receiver,
            'content': message_content,
            'timestamp': timestamp,
            'is_from_webhook': is_from_me,
            'raw_data': message_data
        }

        logger.info("Tentando inserir mensagem no Supabase")
        logger.debug(f"Dados a serem inseridos: {whatsapp_message}")
        result = supabase.table('whatsapp_messages').insert(whatsapp_message).execute()
        
        if result.data:
            logger.info(f"Mensagem do WhatsApp armazenada com sucesso. ID: {result.data[0]['id']}")
            return {"status": "success", "message": "Mensagem armazenada com sucesso"}
        else:
            logger.error("Falha ao armazenar a mensagem do WhatsApp no Supabase")
            return {"status": "error", "message": "Falha ao armazenar a mensagem"}

    except Exception as e:
        logger.error(f"Erro ao processar mensagem do WhatsApp: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}