# app/chatbot/__init__.py (refatorado)
from typing import Dict, Type, Optional
import logging
from .base import BaseChatbot
from .vendas import VendasChatbot
from .treinamento import TreinamentoChatbot
from .whatsapp import WhatsAppChatbot

logger = logging.getLogger("chatbot.factory")

class ChatbotFactory:
    """
    Factory para criar instâncias de chatbots com base no tipo solicitado.
    Implementa o padrão Factory Method.
    """
    
    # Mapeamento de tipos de chatbot para suas classes
    _chatbot_types: Dict[str, Type[BaseChatbot]] = {
        'atual': VendasChatbot,
        'novo': TreinamentoChatbot,
        'whatsapp': WhatsAppChatbot
    }
    
    # Cache de instâncias para reutilização
    _instances: Dict[str, BaseChatbot] = {}
    
    @classmethod
    def create_chatbot(cls, chatbot_type: str) -> Optional[BaseChatbot]:
        """
        Cria ou recupera uma instância de chatbot com base no tipo.
        
        Args:
            chatbot_type: O tipo de chatbot a ser criado ('atual', 'novo', 'whatsapp')
            
        Returns:
            Uma instância de chatbot ou None se o tipo for inválido
        """
        # Verificar se o tipo é válido
        if chatbot_type not in cls._chatbot_types:
            logger.error(f"Tipo de chatbot inválido: {chatbot_type}")
            return None
            
        # Verificar se já existe uma instância no cache
        if chatbot_type in cls._instances:
            logger.info(f"Retornando instância existente de {chatbot_type}")
            return cls._instances[chatbot_type]
            
        # Criar nova instância
        try:
            logger.info(f"Criando nova instância de chatbot: {chatbot_type}")
            chatbot_class = cls._chatbot_types[chatbot_type]
            instance = chatbot_class()
            
            # Armazenar no cache
            cls._instances[chatbot_type] = instance
            return instance
        except Exception as e:
            logger.error(f"Erro ao criar chatbot {chatbot_type}: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def get_available_types(cls) -> list:
        """Retorna a lista de tipos de chatbot disponíveis."""
        return list(cls._chatbot_types.keys())
        
    @classmethod
    def clear_cache(cls) -> None:
        """Limpa o cache de instâncias."""
        cls._instances.clear()
        logger.info("Cache de instâncias de chatbot limpo")