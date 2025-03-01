"""
Chatbot package initialization with new architecture.
This module provides a smooth transition from the old to the new implementation.
"""

from typing import Dict, Optional, Any
import logging
from .factory import (
    get_registry,
    create_chatbot,
    list_available_chatbots,
    ChatbotRegistry
)
from .base_new import BaseChatbot
from ..services.container import get_container
from ..services.logging_service import LoggingService

# Configure package-level logging
logger = LoggingService("chatbot.init")

class ChatbotManager:
    """Manager class for handling chatbot instances and transitions."""
    
    def __init__(self):
        self._registry = get_registry()
        self._container = get_container()
        self._active_chatbots: Dict[str, BaseChatbot] = {}
        self._initialize_logging()
    
    def _initialize_logging(self) -> None:
        """Initialize logging for the chatbot package."""
        logger.info("Initializing chatbot manager")
    
    def get_chatbot(
        self,
        chatbot_type: str,
        create_if_missing: bool = True,
        **kwargs
    ) -> Optional[BaseChatbot]:
        """
        Get a chatbot instance, optionally creating it if it doesn't exist.
        
        Args:
            chatbot_type: Type of chatbot to get/create
            create_if_missing: Whether to create a new instance if none exists
            **kwargs: Additional arguments for chatbot creation
            
        Returns:
            BaseChatbot instance or None if not found and create_if_missing is False
        """
        try:
            # Check if we already have an instance
            if chatbot_type in self._active_chatbots:
                logger.debug(f"Retrieved existing chatbot: {chatbot_type}")
                return self._active_chatbots[chatbot_type]
            
            # Create new instance if requested
            if create_if_missing:
                logger.info(f"Creating new chatbot instance: {chatbot_type}")
                chatbot = create_chatbot(chatbot_type, **kwargs)
                self._active_chatbots[chatbot_type] = chatbot
                return chatbot
            
            logger.warning(f"Chatbot not found and not created: {chatbot_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating chatbot: {str(e)}", exc_info=True)
            raise
    
    def list_chatbots(self) -> Dict[str, str]:
        """List all available chatbot types and their descriptions."""
        return list_available_chatbots()
    
    def get_active_chatbots(self) -> Dict[str, BaseChatbot]:
        """Get all currently active chatbot instances."""
        return self._active_chatbots.copy()
    
    def cleanup(self) -> None:
        """Cleanup resources for all active chatbots."""
        for chatbot_type, chatbot in self._active_chatbots.items():
            try:
                # Implement any necessary cleanup
                logger.info(f"Cleaning up chatbot: {chatbot_type}")
            except Exception as e:
                logger.error(f"Error cleaning up chatbot {chatbot_type}: {str(e)}")
        self._active_chatbots.clear()

# Create global manager instance
_manager = ChatbotManager()

def get_chatbot(chatbot_type: str, **kwargs) -> Optional[BaseChatbot]:
    """
    Convenience function to get/create a chatbot instance.
    
    This function provides backward compatibility with the old implementation
    while using the new architecture internally.
    
    Args:
        chatbot_type: Type of chatbot to get/create
        **kwargs: Additional arguments for chatbot creation
        
    Returns:
        BaseChatbot instance or None if creation fails
    """
    return _manager.get_chatbot(chatbot_type, **kwargs)

def list_chatbots() -> Dict[str, str]:
    """List all available chatbot types."""
    return _manager.list_chatbots()

def get_active_chatbots() -> Dict[str, BaseChatbot]:
    """Get all currently active chatbot instances."""
    return _manager.get_active_chatbots()

def cleanup_chatbots() -> None:
    """Cleanup all active chatbot instances."""
    _manager.cleanup()

# Example usage:
"""
# Get a chatbot instance
vendas_bot = get_chatbot("vendas")

# List available types
available_types = list_chatbots()

# Get all active instances
active_bots = get_active_chatbots()

# Cleanup when done
cleanup_chatbots()
"""

# For backward compatibility
from .vendas_new import VendasChatbot
from .treinamento_new import TreinamentoChatbot
from .whatsapp_new import WhatsAppChatbot

__all__ = [
    'get_chatbot',
    'list_chatbots',
    'get_active_chatbots',
    'cleanup_chatbots',
    'VendasChatbot',
    'TreinamentoChatbot',
    'WhatsAppChatbot'
]
