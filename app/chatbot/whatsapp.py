# app/chatbot/whatsapp.py (refatorado)
from typing import Dict, List, Any, Optional
import logging
from .base import BaseChatbot, client
from config import Config
import json
import asyncio
from functools import lru_cache

logger = logging.getLogger("chatbot.whatsapp")

class WhatsAppChatbot(BaseChatbot):
    """Chatbot para análise de conversas do WhatsApp."""
    
    def __init__(self):
        super().__init__(
            name="Assistente WhatsApp",
            model="gpt-4o",
            assistant_id=Config.ASSISTANT_ID_WHATSAPP
        )
        # Cache para armazenar nomes extraídos
        self._name_cache = {}
    
    def get_instructions(self) -> str:
        return (
            "Você é especialista em análise de conversas do WhatsApp. "
            "Seu objetivo é extrair insights, identificar padrões de comunicação "
            "e ajudar a melhorar a qualidade das interações. Foque em ser preciso "
            "e objetivo em suas análises."
        )
    
    def extract_name(self, message: str) -> Optional[str]:
        """Extrai o nome do usuário usando o modelo de linguagem com cache."""
        # Verificação rápida para mensagens muito curtas
        if len(message.strip()) <= 2 or message.strip().lower() == "é":
            return None
            
        # Verificar cache
        if message in self._name_cache:
            return self._name_cache[message]
                
        try:
            # Usar uma abordagem mais eficiente com uma única chamada à API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Modelo mais leve e rápido para esta tarefa
                messages=[
                    {"role": "system", "content": "Extraia apenas o primeiro nome da pessoa desta mensagem. Responda apenas com o nome, sem pontuação ou frases adicionais. Se não houver nome, responda 'Nenhum'."},
                    {"role": "user", "content": message}
                ],
                max_tokens=10  # Limitar tokens para resposta rápida
            )
            
            extracted = response.choices[0].message.content.strip()
            
            # Validação do nome extraído
            if extracted.lower() in ["nenhum", "none", "não há", "não encontrado"] or len(extracted) <= 2:
                self._name_cache[message] = None
                return None
                
            # Verificar palavras comuns
            common_words = ["oi", "olá", "bom", "boa", "dia", "tarde", "noite", "é", "eh", "sim", "não", "nao"]
            if extracted.lower() in common_words:
                self._name_cache[message] = None
                return None
                
            # Armazenar no cache
            self._name_cache[message] = extracted
            return extracted
            
        except Exception as e:
            logger.error(f"Erro na extração de nome: {e}", exc_info=True)
            return None
    
    @lru_cache(maxsize=20)
    def generate_summary(self, messages_key: str) -> str:
        """Produz um resumo em HTML para as mensagens com cache."""
        try:
            # Desserializar mensagens do formato de chave
            messages = json.loads(messages_key)
            
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
            
    # Método para uso com o cache
    def summarize_messages(self, messages: List[Dict[str, str]]) -> str:
        """Wrapper para usar o cache com generate_summary."""
        # Converter lista para string JSON para usar como chave de cache
        messages_key = json.dumps([
            {"sender_name": m["sender_name"], "content": m["content"]} 
            for m in messages
        ])
        return self.generate_summary(messages_key)