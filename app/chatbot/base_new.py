from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import json
import datetime
from ..services.interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    LoggingServiceInterface
)

class BaseChatbot(ABC):
    """Base class for all chatbots with improved architecture."""
    
    def __init__(
        self,
        name: str,
        model: str,
        ai_service: AIServiceInterface,
        db_service: DatabaseServiceInterface,
        cache_service: CacheServiceInterface,
        logger: LoggingServiceInterface,
        assistant_id: Optional[str] = None
    ):
        self.name = name
        self.model = model
        self.assistant_id = assistant_id
        
        # Inject dependencies
        self._ai_service = ai_service
        self._db_service = db_service
        self._cache_service = cache_service
        self._logger = logger
        
        # Initialize assistant
        self._initialize_assistant()
    
    def _initialize_assistant(self) -> None:
        """Initialize or retrieve the OpenAI assistant."""
        cache_key = f"assistant:{self.name}"
        
        # Try to get assistant from cache
        if self.assistant_id:
            cached_assistant = self._cache_service.get(cache_key)
            if cached_assistant:
                self._logger.info(f"Retrieved assistant from cache: {self.name}")
                return
        
        try:
            if not self.assistant_id:
                self._create_new_assistant()
            else:
                self._retrieve_existing_assistant()
            
            # Cache the assistant details
            self._cache_service.set(
                cache_key,
                {
                    "id": self.assistant_id,
                    "name": self.name,
                    "model": self.model
                },
                ttl=3600  # Cache for 1 hour
            )
            
        except Exception as e:
            self._logger.error(f"Error initializing assistant: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to initialize assistant {self.name}: {str(e)}")
    
    def _create_new_assistant(self) -> None:
        """Create a new assistant with configurations."""
        self._logger.info(f"Creating new assistant: {self.name}")
        assistant = self._ai_service.create_assistant(
            name=self.name,
            instructions=self.get_instructions(),
            model=self.model
        )
        self.assistant_id = assistant.id
        self._logger.info(f"Created new assistant with ID: {self.assistant_id}")
    
    def _retrieve_existing_assistant(self) -> None:
        """Retrieve an existing assistant."""
        self._logger.info(f"Retrieving existing assistant: {self.assistant_id}")
        # The AI service will handle the actual retrieval
        # We just need to verify the assistant exists
        self._ai_service.get_assistant(self.assistant_id)
    
    @abstractmethod
    def get_instructions(self) -> str:
        """Get assistant instructions. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools. Must be implemented by subclasses."""
        pass
    
    def create_thread(self) -> str:
        """Create a new conversation thread with caching."""
        try:
            thread_id = self._ai_service.create_thread()
            self._logger.info(f"Created new thread: {thread_id}")
            return thread_id
        except Exception as e:
            self._logger.error(f"Error creating thread: {str(e)}", exc_info=True)
            raise
    
    def process_message(
        self,
        thread_id: str,
        message: str,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and return the response."""
        try:
            # Log incoming message
            self._logger.info(
                f"Processing message in thread {thread_id}",
                extra={"user_name": user_name, "message_length": len(message)}
            )
            
            # Send message to AI service
            message_response = self._ai_service.send_message(thread_id, message)
            
            # Log the interaction in database
            self._db_service.log_interaction({
                "thread_id": thread_id,
                "role": "user",
                "content": message,
                "user_name": user_name or "anonymous",
                "chatbot_type": self.name,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Process the response
            response = self._process_and_log_response(thread_id, message_response)
            
            return response
            
        except Exception as e:
            self._logger.error(
                f"Error processing message: {str(e)}",
                exc_info=True,
                extra={"thread_id": thread_id}
            )
            return {
                "error": str(e),
                "thread_id": thread_id
            }
    
    def _process_and_log_response(
        self,
        thread_id: str,
        message_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process the AI response and log it."""
        try:
            # Get the response content
            response_content = message_response.get("content", "")
            
            # Log the interaction
            self._db_service.log_interaction({
                "thread_id": thread_id,
                "role": "assistant",
                "content": response_content,
                "chatbot_type": self.name,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            return {
                "response": response_content,
                "thread_id": thread_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(
                f"Error processing response: {str(e)}",
                exc_info=True,
                extra={"thread_id": thread_id}
            )
            return {
                "error": str(e),
                "thread_id": thread_id
            }
    
    def get_chat_history(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get chat history for a thread."""
        try:
            # Try to get from cache first
            cache_key = f"chat_history:{thread_id}"
            cached_history = self._cache_service.get(cache_key)
            
            if cached_history:
                self._logger.debug(f"Retrieved chat history from cache: {thread_id}")
                return cached_history
            
            # Get from database if not in cache
            history = self._db_service.get_chat_history(thread_id, limit)
            
            # Cache the result
            self._cache_service.set(cache_key, history, ttl=300)  # Cache for 5 minutes
            
            return history
            
        except Exception as e:
            self._logger.error(
                f"Error retrieving chat history: {str(e)}",
                exc_info=True,
                extra={"thread_id": thread_id}
            )
            return []
    
    def extract_name(self, message: str) -> Optional[str]:
        """Extract user name from message using cache."""
        try:
            # Check cache first
            cache_key = f"extracted_name:{hash(message)}"
            cached_name = self._cache_service.get(cache_key)
            
            if cached_name is not None:
                return cached_name
            
            # Use AI service to extract name
            extracted_name = self._ai_service.extract_name(message)
            
            # Cache the result
            self._cache_service.set(cache_key, extracted_name, ttl=3600)
            
            return extracted_name
            
        except Exception as e:
            self._logger.error(f"Error extracting name: {str(e)}", exc_info=True)
            return None
