from supabase import create_client
from config import Config

# Inicializar o cliente Supabase
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def process_whatsapp_message(message_data):
    try:
        # Extrair informações relevantes da mensagem
        sender = message_data.get('from', 'Desconhecido')
        message_content = message_data.get('text', {}).get('body', '')
        timestamp = message_data.get('timestamp', '')

        # Preparar os dados para inserção no Supabase
        whatsapp_message = {
            'sender': sender,
            'content': message_content,
            'timestamp': timestamp,
            'raw_data': message_data  # Armazenar o payload completo para referência futura
        }

        # Inserir a mensagem no Supabase
        result = supabase.table('whatsapp_messages').insert(whatsapp_message).execute()

        if result.data:
            print(f"Mensagem do WhatsApp armazenada com sucesso. ID: {result.data[0]['id']}")
            return {"status": "success", "message": "Mensagem armazenada com sucesso"}
        else:
            print("Falha ao armazenar a mensagem do WhatsApp")
            return {"status": "error", "message": "Falha ao armazenar a mensagem"}

    except Exception as e:
        print(f"Erro ao processar mensagem do WhatsApp: {e}")
        return {"status": "error", "message": "Erro ao processar a mensagem"}