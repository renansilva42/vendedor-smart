import logging
import sys
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from .interfaces import LoggingServiceInterface
from config import Config

class LoggingService(LoggingServiceInterface):
    """Centralized logging service implementation."""
    
    def __init__(self, app_name: str = "chatbot", log_level: int = logging.INFO):
        self.app_name = app_name
        self.log_level = log_level
        self._configure_logging()
        self.logger = logging.getLogger(app_name)
    
    def _configure_logging(self) -> None:
        """Configure logging with both file and console handlers."""
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{self.app_name}_{timestamp}.log")
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers = []
        
        # Add rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Set logging level from config
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    def _format_extra(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format extra fields for logging."""
        base_extra = {
            "app_name": self.app_name,
            "timestamp": datetime.now().isoformat()
        }
        if extra:
            base_extra.update(extra)
        return base_extra
    
    def info(self, message: str, **kwargs) -> None:
        """Log info level message."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error level message."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning level message."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug level message."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.debug(message, extra=extra)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.exception(message, extra=extra)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical level message."""
        extra = self._format_extra(kwargs.get("extra"))
        self.logger.critical(message, extra=extra)

class ChatbotLogger(LoggingService):
    """Specialized logger for chatbot operations."""
    
    def __init__(self, chatbot_name: str):
        super().__init__(f"chatbot.{chatbot_name}")
        self.chatbot_name = chatbot_name
    
    def _format_extra(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add chatbot-specific fields to logging extra."""
        base_extra = super()._format_extra(extra)
        base_extra.update({
            "chatbot_name": self.chatbot_name,
            "environment": Config.ENVIRONMENT
        })
        return base_extra
    
    def log_interaction(self, thread_id: str, role: str, content: str, **kwargs) -> None:
        """Log a chatbot interaction."""
        extra = {
            "thread_id": thread_id,
            "role": role,
            "interaction_type": "message"
        }
        extra.update(kwargs)
        self.info(f"{role}: {content[:100]}...", extra=extra)
    
    def log_error_interaction(self, thread_id: str, error: Exception, **kwargs) -> None:
        """Log a chatbot error interaction."""
        extra = {
            "thread_id": thread_id,
            "interaction_type": "error",
            "error_type": type(error).__name__
        }
        extra.update(kwargs)
        self.error(str(error), exc_info=True, extra=extra)
