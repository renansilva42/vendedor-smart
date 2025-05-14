from typing import Dict, Type, Any
from .base import BaseChatbot
from .vendas import VendasChatbot
from .treinamento import TreinamentoChatbot
from .whatsapp import WhatsAppChatbot
from ..services.container import ServiceContainer, get_container
from ..services.interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    LoggingServiceInterface
)

class ChatbotRegistry:
    """Registry for managing chatbot types and their creation."""
    
    def __init__(self):
        self._chatbots: Dict[str, Type[BaseChatbot]] = {}
        self._container = get_container()
        self._initialize_registry()
    
    def _initialize_registry(self) -> None:
        """Initialize the default chatbot registry."""
        self.register_chatbot("vendas", VendasChatbot)
        self.register_chatbot("treinamento", TreinamentoChatbot)
        self.register_chatbot("whatsapp", WhatsAppChatbot)
    
    def register_chatbot(self, name: str, chatbot_class: Type[BaseChatbot]) -> None:
        """Register a new chatbot type."""
        if not issubclass(chatbot_class, BaseChatbot):
            raise ValueError(f"Chatbot class must inherit from BaseChatbot: {chatbot_class}")
        self._chatbots[name] = chatbot_class
    
    def get_chatbot_class(self, name: str) -> Type[BaseChatbot]:
        """Get a registered chatbot class by name."""
        if name not in self._chatbots:
            raise ValueError(f"Unknown chatbot type: {name}")
        return self._chatbots[name]
    
    def create_chatbot(self, name: str, **kwargs) -> BaseChatbot:
        """Create a new chatbot instance with injected dependencies."""
        chatbot_class = self.get_chatbot_class(name)
        
        # Get required services from container
        services = {
            "ai_service": self._container.get(AIServiceInterface),
            "db_service": self._container.get(DatabaseServiceInterface),
            "cache_service": self._container.get(CacheServiceInterface),
            "logger": self._container.create_logger(f"chatbot.{name}")
        }
        
        # Create chatbot instance with services and additional kwargs
        return chatbot_class(**services, **kwargs)
    
    def list_chatbots(self) -> Dict[str, str]:
        """List all registered chatbot types and their descriptions."""
        return {
            name: chatbot_class.__doc__ or "No description available"
            for name, chatbot_class in self._chatbots.items()
        }

# Create global registry instance
_registry = None

def get_registry() -> ChatbotRegistry:
    """Get the global chatbot registry instance."""
    global _registry
    if _registry is None:
        _registry = ChatbotRegistry()
    return _registry

def create_chatbot(name: str, **kwargs) -> BaseChatbot:
    """Convenience function to create a chatbot instance."""
    return get_registry().create_chatbot(name, **kwargs)

def list_available_chatbots() -> Dict[str, str]:
    """Convenience function to list available chatbot types."""
    return get_registry().list_chatbots()

# Example usage:
"""
# Get registry instance
registry = get_registry()

# Create chatbot instances
vendas_bot = registry.create_chatbot("vendas")
treinamento_bot = registry.create_chatbot("treinamento")
whatsapp_bot = registry.create_chatbot("whatsapp")

# Or use convenience functions
vendas_bot = create_chatbot("vendas")
available_bots = list_available_chatbots()
"""
