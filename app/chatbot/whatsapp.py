# app/chatbot/whatsapp.py
from typing import Dict, List, Any, Optional
import logging
from .base import BaseChatbot, client
from config import Config

logger = logging.getLogger("chatbot.whatsapp")

class WhatsAppChatbot(BaseChatbot):
    """Chatbot para análise de conversas do WhatsApp."""
    
    def __init__(self):
        super().__init__(
            name="Assistente WhatsApp",
            model="gpt-4o",
            assistant_id=Config.ASSISTANT_ID_WHATSAPP
        )
    
    def get_instructions(self) -> str:
        return (
            "Você é especialista em análise de conversas do WhatsApp. "
            "Seu objetivo é extrair insights, identificar padrões de comunicação "
            "e ajudar a melhorar a qualidade das interações. Foque em ser preciso "
            "e objetivo em suas análises."
        )
    
    def extract_name(self, message: str) -> Optional[str]:
        """Extrai o nome do usuário usando o modelo de linguagem."""
        try:
            temp_thread = self.create_thread()
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content="Você é um especialista em extrair nomes. Retorne apenas o primeiro nome encontrado ou 'Nenhum nome encontrado'."
            )
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content=f"Extraia o nome desta mensagem: '{message}'"
            )
            run = client.beta.threads.runs.create(
                thread_id=temp_thread,
                assistant_id=self.assistant_id
            )
            
            # Esperar pela conclusão
            max_attempts = 30
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=temp_thread,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    logger.error("Falha na extração de nome")
                    return None
                import time
                time.sleep(1)
            
            msgs = client.beta.threads.messages.list(thread_id=temp_thread)
            if msgs.data:
                extracted = msgs.data[0].content[0].text.value.strip()
                return None if "nenhum" in extracted.lower() else extracted
            return None
        except Exception as e:
            logger.error(f"Erro na extração de nome: {e}", exc_info=True)
            return None
    
    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """Produz um resumo em HTML para as mensagens."""
        try:
            system_msg = (
                "Você é um analista de textos. Formate o resumo em HTML usando: "
                "<h3> para títulos, <ul>/<li> para listas e <strong> para destaques."
            )
            user_msg = "Resuma:\n\n" + "\n".join(
                f"{m['sender_name']}: {m['content']}" for m in messages
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}", exc_info=True)
            return f"<h3>Erro ao gerar resumo</h3><p>{str(e)}</p>"