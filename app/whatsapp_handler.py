import logging
from supabase import create_client
from config import Config

# Configuração de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar o cliente Supabase
logger.info(f"Tentando conectar ao Supabase: {Config.SUPABASE_URL}")
try:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    logger.info("Conexão com Supabase estabelecida com sucesso")
except Exception as e:
    logger.error(f"Erro ao conectar com Supabase: {e}", exc_info=True)

def process_whatsapp_message(message_data):
    logger.info("Iniciando processamento da mensagem do WhatsApp")
    try:
        # Extrair informações relevantes da mensagem
        logger.debug(f"Dados da mensagem: {message_data}")
        
        # Adapte estas linhas de acordo com a estrutura real dos dados recebidos
        sender = message_data.get('from', 'Desconhecido')
        message_content = message_data.get('text', {}).get('body', '')
        timestamp = message_data.get('timestamp', '')

        logger.info(f"Mensagem recebida de: {sender}")
        logger.debug(f"Conteúdo da mensagem: {message_content}")
        logger.debug(f"Timestamp: {timestamp}")

        # Preparar os dados para inserção no Supabase
        whatsapp_message = {
            'sender': sender,
            'content': message_content,
            'timestamp': timestamp,
            'raw_data': message_data  # Armazenar o payload completo para referência futura
        }

        logger.info("Tentando inserir mensagem no Supabase")
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