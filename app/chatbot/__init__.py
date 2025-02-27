# app/chatbot/__init__.py
from .vendas import VendasChatbot
from .treinamento import TreinamentoChatbot
from .whatsapp import WhatsAppChatbot

class ChatbotFactory:
    """Fábrica para criar instâncias de chatbots."""
    
    @staticmethod
    def create_chatbot(chatbot_type: str):
        """Cria e retorna uma instância do chatbot especificado."""
        if chatbot_type == "atual":
            return VendasChatbot()
        elif chatbot_type == "novo":
            return TreinamentoChatbot()
        elif chatbot_type == "whatsapp":
            return WhatsAppChatbot()
        else:
            raise ValueError(f"Tipo de chatbot desconhecido: {chatbot_type}")