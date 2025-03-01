from typing import Dict, List, Any, Optional
import json
from .base_new import BaseChatbot
from ..services.interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    LoggingServiceInterface
)
from config import Config

class WhatsAppChatbot(BaseChatbot):
    """Refactored WhatsApp analysis chatbot with improved architecture."""
    
    def __init__(
        self,
        ai_service: AIServiceInterface,
        db_service: DatabaseServiceInterface,
        cache_service: CacheServiceInterface,
        logger: LoggingServiceInterface
    ):
        super().__init__(
            name="Assistente WhatsApp",
            model="gpt-4o",
            ai_service=ai_service,
            db_service=db_service,
            cache_service=cache_service,
            logger=logger,
            assistant_id=Config.ASSISTANT_ID_WHATSAPP
        )
    
    def get_instructions(self) -> str:
        """Get specialized instructions for the WhatsApp analysis assistant."""
        return (
            "Você é um especialista em análise de conversas do WhatsApp. "
            "\n\nSuas principais responsabilidades:\n"
            "1. Analisar padrões de comunicação\n"
            "2. Identificar pontos de melhoria\n"
            "3. Extrair insights relevantes\n"
            "4. Sugerir otimizações na comunicação\n"
            "5. Gerar relatórios analíticos\n"
            "\nFoco em:\n"
            "- Tempo de resposta\n"
            "- Clareza na comunicação\n"
            "- Efetividade das mensagens\n"
            "- Padrões de engajamento\n"
            "- Satisfação do cliente\n"
            "\nForneça análises:\n"
            "- Objetivas e baseadas em dados\n"
            "- Com recomendações práticas\n"
            "- Focadas em resultados mensuráveis"
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get specialized tools for the WhatsApp analysis assistant."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_conversation_metrics",
                    "description": "Analisa métricas de uma conversa do WhatsApp",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chat_id": {
                                "type": "string",
                                "description": "ID da conversa"
                            },
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Métricas a serem analisadas"
                            }
                        },
                        "required": ["chat_id", "metrics"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_conversation_summary",
                    "description": "Gera um resumo estruturado de uma conversa",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chat_id": {
                                "type": "string",
                                "description": "ID da conversa"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["short", "detailed", "topics"],
                                "description": "Formato do resumo"
                            }
                        },
                        "required": ["chat_id", "format"]
                    }
                }
            }
        ]
    
    def analyze_conversation(
        self,
        chat_id: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Analyze WhatsApp conversation metrics."""
        try:
            cache_key = f"analysis:{chat_id}:{','.join(sorted(metrics))}"
            cached_analysis = self._cache_service.get(cache_key)
            
            if cached_analysis:
                self._logger.debug(f"Retrieved analysis from cache: {chat_id}")
                return cached_analysis
            
            # Get conversation data
            conversation = self._db_service.query_messages({
                "chat_id": chat_id,
                "limit": 100  # Analyze last 100 messages
            })
            
            if not conversation:
                return {"error": "No conversation data found"}
            
            # Prepare analysis context
            analysis_context = {
                "messages": conversation,
                "metrics": metrics,
                "metadata": {
                    "chat_id": chat_id,
                    "message_count": len(conversation),
                    "time_range": self._get_conversation_timerange(conversation)
                }
            }
            
            # Use AI to analyze conversation
            analysis = self._ai_service.analyze_conversation(analysis_context)
            
            # Structure the results
            results = {
                "chat_id": chat_id,
                "timestamp": self._get_current_timestamp(),
                "metrics": analysis.get("metrics", {}),
                "insights": analysis.get("insights", []),
                "recommendations": analysis.get("recommendations", [])
            }
            
            # Cache the results
            self._cache_service.set(cache_key, results, ttl=1800)  # 30 minutes
            
            # Store analysis results
            self._db_service.save_analysis_result(results)
            
            return results
            
        except Exception as e:
            self._logger.error(
                f"Error analyzing conversation: {str(e)}",
                exc_info=True,
                extra={"chat_id": chat_id}
            )
            return {"error": str(e)}
    
    def generate_summary(
        self,
        chat_id: str,
        format: str = "detailed"
    ) -> Dict[str, Any]:
        """Generate a structured summary of a WhatsApp conversation."""
        try:
            cache_key = f"summary:{chat_id}:{format}"
            cached_summary = self._cache_service.get(cache_key)
            
            if cached_summary:
                return cached_summary
            
            # Get conversation messages
            messages = self._db_service.query_messages({
                "chat_id": chat_id,
                "limit": 100
            })
            
            if not messages:
                return {"error": "No messages found"}
            
            # Prepare summary context
            summary_context = {
                "messages": messages,
                "format": format,
                "metadata": {
                    "chat_id": chat_id,
                    "message_count": len(messages),
                    "timerange": self._get_conversation_timerange(messages)
                }
            }
            
            # Generate summary using AI
            summary = self._ai_service.generate_summary(summary_context)
            
            # Structure the results
            results = {
                "chat_id": chat_id,
                "format": format,
                "timestamp": self._get_current_timestamp(),
                "summary": summary.get("content", ""),
                "topics": summary.get("topics", []),
                "key_points": summary.get("key_points", [])
            }
            
            # Cache the results
            self._cache_service.set(cache_key, results, ttl=3600)  # 1 hour
            
            return results
            
        except Exception as e:
            self._logger.error(
                f"Error generating summary: {str(e)}",
                exc_info=True,
                extra={"chat_id": chat_id}
            )
            return {"error": str(e)}
    
    def _get_conversation_timerange(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Get the time range of a conversation."""
        if not messages:
            return {"start": None, "end": None}
        
        timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
        if not timestamps:
            return {"start": None, "end": None}
        
        return {
            "start": min(timestamps),
            "end": max(timestamps)
        }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
