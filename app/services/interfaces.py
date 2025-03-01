from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from openai import OpenAI

class AIServiceInterface(ABC):
    """Interface for AI service operations."""
    
    @abstractmethod
    def create_assistant(self, name: str, instructions: str, model: str) -> Any:
        """Create a new AI assistant."""
        pass
    
    @abstractmethod
    def create_thread(self) -> str:
        """Create a new conversation thread."""
        pass
    
    @abstractmethod
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Send a message to the AI."""
        pass
    
    @abstractmethod
    def process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Process a run and get the response."""
        pass

class DatabaseServiceInterface(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def log_interaction(self, data: Dict[str, Any]) -> bool:
        """Log an interaction to the database."""
        pass
    
    @abstractmethod
    def query_messages(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query messages with filters."""
        pass

class CacheServiceInterface(ABC):
    """Interface for caching operations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

class LoggingServiceInterface(ABC):
    """Interface for logging operations."""
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info level message."""
        pass
    
    @abstractmethod
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error level message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning level message."""
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug level message."""
        pass
