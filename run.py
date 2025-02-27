from app import create_app
from app.models import supabase
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os


# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Teste de conexão com o Supabase
try:
    response = supabase.table('usuarios_chatbot').select('*').limit(1).execute()
    print("Conexão com Supabase bem-sucedida!")
    print(f"Resposta: {response}")
except Exception as e:
    print(f"Erro ao conectar com Supabase: {e}", file=sys.stderr)
    sys.exit(1)

def delete_whatsapp_messages():
    try:
        # Deletar todas as mensagens da tabela whatsapp_messages
        result = supabase.table('whatsapp_messages').delete().execute()
        
        # Verificar se a operação foi bem-sucedida
        if result.data is not None:
            logger.info(f"Todas as mensagens foram deletadas com sucesso.")
        else:
            logger.warning("Nenhuma mensagem foi deletada ou ocorreu um erro.")
        
    except Exception as e:
        logger.error(f"Erro ao deletar mensagens: {e}", exc_info=True)

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
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)