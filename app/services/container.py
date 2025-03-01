from typing import Dict, Type, Any, Optional
from .interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    LoggingServiceInterface
)
from .ai_service import OpenAIService
from .database_service import SupabaseService
from .cache_service import MemoryCacheService, JSONSerializableCacheService
from .logging_service import LoggingService, ChatbotLogger

class ServiceContainer:
    """Container for managing service dependencies."""
    
    _instance = None
    _services: Dict[Type, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceContainer, cls).__new__(cls)
            cls._instance._initialize_services()
        return cls._instance
    
    def _initialize_services(self) -> None:
        """Initialize default service implementations."""
        self._services = {
            AIServiceInterface: OpenAIService(),
            DatabaseServiceInterface: SupabaseService(),
            CacheServiceInterface: JSONSerializableCacheService(),
            LoggingServiceInterface: LoggingService()
        }
    
    def get(self, service_type: Type) -> Any:
        """Get service instance by type."""
        if service_type not in self._services:
            raise KeyError(f"Service not registered: {service_type.__name__}")
        return self._services[service_type]
    
    def register(self, service_type: Type, implementation: Any) -> None:
        """Register a service implementation."""
        self._services[service_type] = implementation
    
    def create_logger(self, name: str) -> LoggingServiceInterface:
        """Create a specialized logger instance."""
        return ChatbotLogger(name)

class ChatbotFactory:
    """Factory for creating chatbot instances."""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self._chatbot_types: Dict[str, Type] = {}
    
    def register_chatbot(self, name: str, chatbot_class: Type) -> None:
        """Register a chatbot type."""
        self._chatbot_types[name] = chatbot_class
    
    def create_chatbot(self, chatbot_type: str, **kwargs) -> Any:
        """Create a chatbot instance with injected dependencies."""
        if chatbot_type not in self._chatbot_types:
            raise ValueError(f"Unknown chatbot type: {chatbot_type}")
        
        # Get required services
        ai_service = self.container.get(AIServiceInterface)
        db_service = self.container.get(DatabaseServiceInterface)
        cache_service = self.container.get(CacheServiceInterface)
        logger = self.container.create_logger(f"chatbot.{chatbot_type}")
        
        # Create chatbot instance with dependencies
        chatbot_class = self._chatbot_types[chatbot_type]
        return chatbot_class(
            ai_service=ai_service,
            db_service=db_service,
            cache_service=cache_service,
            logger=logger,
            **kwargs
        )

# Create global instances
container = ServiceContainer()
chatbot_factory = ChatbotFactory(container)

def get_container() -> ServiceContainer:
    """Get the global service container instance."""
    return container

def get_chatbot_factory() -> ChatbotFactory:
    """Get the global chatbot factory instance."""
    return chatbot_factory
