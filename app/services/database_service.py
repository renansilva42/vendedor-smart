from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from supabase import create_client, Client
from .interfaces import DatabaseServiceInterface
from config import Config

logger = logging.getLogger(__name__)

class SupabaseService(DatabaseServiceInterface):
    """Implementation of database service using Supabase."""
    
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
    def log_interaction(self, data: Dict[str, Any]) -> bool:
        """Log an interaction to the database."""
        try:
            # Ensure required fields are present
            required_fields = ['thread_id', 'role', 'content', 'user_name', 'chatbot_type']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Insert the interaction record
            result = self.client.table('mensagens_chatbot').insert(data).execute()
            
            if result.data:
                logger.info(f"Interaction logged successfully: {result.data[0].get('id')}")
                return True
            else:
                logger.warning("No data returned from interaction logging")
                return False
                
        except Exception as e:
            logger.error(f"Failed to log interaction: {str(e)}")
            return False
    
    def query_messages(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query messages with filters."""
        try:
            query = self.client.table('whatsapp_messages').select('*')
            
            # Apply filters
            if filters.get('sender_name'):
                query = query.ilike('sender_name', f"%{filters['sender_name']}%")
            
            if filters.get('content'):
                query = query.ilike('content', f"%{filters['content']}%")
            
            if filters.get('start_date') and filters.get('end_date'):
                query = query.gte('timestamp', filters['start_date'])\
                           .lte('timestamp', filters['end_date'])
            
            # Apply sorting
            query = query.order('timestamp', desc=True)
            
            # Apply limit
            if filters.get('limit'):
                query = query.limit(filters['limit'])
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} messages")
                return self._format_messages(result.data)
            else:
                logger.info("No messages found matching filters")
                return []
                
        except Exception as e:
            logger.error(f"Failed to query messages: {str(e)}")
            return []
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format messages for consistent output."""
        formatted = []
        for msg in messages:
            formatted.append({
                "id": msg.get("id"),
                "sender": msg.get("sender_name", "Unknown"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp"),
                "metadata": {
                    "type": msg.get("type"),
                    "status": msg.get("status"),
                    "chat_id": msg.get("chat_id")
                }
            })
        return formatted
    
    def get_chat_history(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chat history for a specific thread."""
        try:
            result = self.client.table('mensagens_chatbot')\
                              .select('*')\
                              .eq('thread_id', thread_id)\
                              .order('timestamp', desc=True)\
                              .limit(limit)\
                              .execute()
            
            if result.data:
                logger.info(f"Retrieved {len(result.data)} messages for thread {thread_id}")
                return self._format_messages(result.data)
            else:
                logger.info(f"No messages found for thread {thread_id}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get chat history: {str(e)}")
            return []
    
    def save_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """Save analysis results to the database."""
        try:
            result = self.client.table('analysis_results').insert({
                **analysis_data,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                logger.info(f"Analysis result saved: {result.data[0].get('id')}")
                return True
            else:
                logger.warning("No data returned from analysis save")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save analysis result: {str(e)}")
            return False
