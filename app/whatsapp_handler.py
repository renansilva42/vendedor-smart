from openai import OpenAI
from config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def process_whatsapp_message(message_data):
    try:
        # Criar uma nova thread para cada conversa
        thread = client.beta.threads.create()

        # Adicionar a mensagem do usuário à thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_data
        )

        # Executar o assistente específico do WhatsApp
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=Config.ASSISTANT_ID_WHATSAPP
        )

        # Aguardar a conclusão da execução
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "failed":
            return "Desculpe, ocorreu um erro ao processar sua mensagem."

        # Recuperar a resposta do assistente
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]

        if assistant_messages:
            # Pega a mensagem mais recente do assistente
            latest_message = assistant_messages[0]
            return latest_message.content[0].text.value
        else:
            return "Não foi possível obter uma resposta do assistente."

    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde."