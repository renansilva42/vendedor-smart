from typing import Dict, List, Any, Optional
from openai import OpenAI
import time
import json
from functools import wraps
import logging
from .interfaces import AIServiceInterface
from config import Config

logger = logging.getLogger(__name__)

def retry_on_exception(retries: int = 3, delay: int = 2):
    """Decorator for implementing retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # Last attempt
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(delay ** attempt)  # Exponential backoff
            return None
        return wrapper
    return decorator

class OpenAIService(AIServiceInterface):
    """Implementation of AI service using OpenAI."""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    @retry_on_exception()
    def create_assistant(self, name: str, instructions: str, model: str) -> Any:
        """Create a new OpenAI assistant."""
        try:
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model
            )
            logger.info(f"Assistant created successfully: {name}")
            return assistant
        except Exception as e:
            logger.error(f"Failed to create assistant: {str(e)}")
            raise
    
    @retry_on_exception()
    def create_thread(self) -> str:
        """Create a new conversation thread."""
        try:
            thread = self.client.beta.threads.create()
            logger.info(f"Thread created: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Failed to create thread: {str(e)}")
            raise
    
    @retry_on_exception()
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Send a message to the thread."""
        try:
            response = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            logger.debug(f"Message sent to thread {thread_id}")
            return {
                "id": response.id,
                "content": response.content[0].text.value if response.content else "",
                "thread_id": thread_id
            }
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
    
    def process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Process a run and handle required actions."""
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run_status.status == 'completed':
                    return self._get_completion_response(thread_id)
                
                elif run_status.status == 'failed':
                    error_msg = getattr(run_status, 'last_error', {'message': 'Unknown error'}).message
                    logger.error(f"Run failed: {error_msg}")
                    return {"error": error_msg, "thread_id": thread_id}
                
                elif run_status.status == 'requires_action':
                    self._handle_required_actions(thread_id, run_id, run_status)
                
                elif run_status.status in ['queued', 'in_progress']:
                    time.sleep(1)
                    continue
                
            except Exception as e:
                logger.error(f"Error processing run: {str(e)}")
                return {"error": str(e), "thread_id": thread_id}
            
        return {"error": "Processing timeout", "thread_id": thread_id}
    
    def _get_completion_response(self, thread_id: str) -> Dict[str, Any]:
        """Get the final response from a completed run."""
        try:
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            if not messages.data:
                return {"error": "No messages found", "thread_id": thread_id}
            
            return {
                "response": messages.data[0].content[0].text.value,
                "thread_id": thread_id,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error getting completion response: {str(e)}")
            return {"error": str(e), "thread_id": thread_id}
    
    def _handle_required_actions(self, thread_id: str, run_id: str, run_status: Any) -> None:
        """Handle any required actions from the assistant."""
        try:
            tool_outputs = []
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                # Note: Tool execution should be handled by a separate service
                # This is a placeholder for the tool execution logic
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": "completed"})
                })
            
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )
        except Exception as e:
            logger.error(f"Error handling required actions: {str(e)}")
            raise
