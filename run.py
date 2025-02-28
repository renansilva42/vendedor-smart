# run.py (refatorado)
from app import create_app
from app.models import supabase
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os
import atexit
from app.chatbot import ChatbotFactory

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Testa a conexão com o banco de dados Supabase."""
    try:
        response = supabase.table('usuarios_chatbot').select('*').limit(1).execute()
        logger.info("Conexão com Supabase bem-sucedida!")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar com Supabase: {str(e)}")
        return False

def delete_whatsapp_messages():
    """Deleta todas as mensagens da tabela whatsapp_messages."""
    try:
        result = supabase.table('whatsapp_messages').delete().execute()
        
        if result.data is not None:
            logger.info(f"Todas as mensagens do WhatsApp foram deletadas com sucesso.")
        else:
            logger.warning("Nenhuma mensagem do WhatsApp foi deletada ou ocorreu um erro.")
        
    except Exception as e:
        logger.error(f"Erro ao deletar mensagens do WhatsApp: {e}", exc_info=True)

def cleanup_resources():
    """Limpa recursos antes de encerrar a aplicação."""
    logger.info("Limpando recursos...")
    
    # Limpar cache de chatbots
    ChatbotFactory.clear_cache()
    
    # Encerrar scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler encerrado.")

# Verificar conexão com o banco de dados
if not test_database_connection():
    logger.critical("Não foi possível conectar ao banco de dados. Encerrando aplicação.")
    sys.exit(1)

# Criar aplicação Flask
app = create_app()

# Configurar o agendador
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=delete_whatsapp_messages,
    trigger=CronTrigger(hour=23, minute=59, second=59),
    id='delete_whatsapp_messages_job',
    name='Delete WhatsApp messages daily at 23:59:59',
    replace_existing=True
)

# Iniciar o scheduler
try:
    scheduler.start()
    logger.info("Scheduler iniciado com sucesso.")
except Exception as e:
    logger.error(f"Erro ao iniciar scheduler: {e}", exc_info=True)

# Registrar função de limpeza para ser executada ao encerrar a aplicação
atexit.register(cleanup_resources)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)