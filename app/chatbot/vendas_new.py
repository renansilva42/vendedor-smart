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

class VendasChatbot(BaseChatbot):
    """Refactored Vendas (Sales) chatbot with improved architecture."""
    
    def __init__(
        self,
        ai_service: AIServiceInterface,
        db_service: DatabaseServiceInterface,
        cache_service: CacheServiceInterface,
        logger: LoggingServiceInterface
    ):
        super().__init__(
            name="Assistente de Vendas (Mentor)",
            model="gpt-4o",
            ai_service=ai_service,
            db_service=db_service,
            cache_service=cache_service,
            logger=logger,
            assistant_id=Config.ASSISTANT_ID_VENDAS
        )
    
    def get_instructions(self) -> str:
        """Get specialized instructions for the sales assistant."""
        return (
            "Você é um especialista em vendas, atuando como mentor para vendedores. "
            "Seu objetivo é ajudar a melhorar as técnicas de vendas, oferecer dicas "
            "e analisar conversas anteriores para identificar pontos de melhoria. "
            "\n\nDiretrizes específicas:\n"
            "1. Sempre mantenha um tom profissional e construtivo\n"
            "2. Foque em feedback acionável e específico\n"
            "3. Use exemplos práticos quando possível\n"
            "4. Sugira técnicas de vendas comprovadas\n"
            "5. Analise padrões de comunicação e sugira melhorias\n"
            "\nUse as ferramentas disponíveis para:\n"
            "- Consultar histórico de conversas do WhatsApp\n"
            "- Analisar métricas de vendas\n"
            "- Registrar interações importantes\n"
            "- Gerar relatórios de progresso"
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get specialized tools for the sales assistant."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_whatsapp_messages",
                    "description": "Consulta históricos do WhatsApp com filtros por remetente, conteúdo e datas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sender_name": {
                                "type": "string",
                                "description": "Nome do remetente para filtrar"
                            },
                            "content": {
                                "type": "string",
                                "description": "Texto para buscar nas mensagens"
                            },
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Data inicial (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Data final (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Número máximo de mensagens"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_sales_metrics",
                    "description": "Analisa métricas de vendas para um período específico",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Data inicial da análise"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Data final da análise"
                            },
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de métricas para analisar"
                            }
                        },
                        "required": ["start_date", "end_date", "metrics"]
                    }
                }
            }
        ]
    
    def analyze_conversation(
        self,
        thread_id: str,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Analyze a conversation thread and provide insights."""
        try:
            # Check cache first
            cache_key = f"analysis:{thread_id}:{analysis_type}"
            cached_analysis = self._cache_service.get(cache_key)
            
            if cached_analysis:
                self._logger.debug(f"Retrieved analysis from cache: {thread_id}")
                return cached_analysis
            
            # Get conversation history
            history = self.get_chat_history(thread_id)
            
            if not history:
                return {"error": "No conversation history found"}
            
            # Prepare analysis prompt based on type
            analysis_prompts = {
                "general": "Analise esta conversa de vendas e identifique pontos fortes e áreas de melhoria.",
                "technique": "Avalie as técnicas de vendas utilizadas nesta conversa.",
                "objections": "Identifique as objeções do cliente e como foram tratadas.",
                "closing": "Analise as tentativas de fechamento e sua eficácia."
            }
            
            prompt = analysis_prompts.get(
                analysis_type,
                analysis_prompts["general"]
            )
            
            # Use AI service to analyze
            analysis = self._ai_service.analyze_conversation(
                history,
                prompt,
                max_tokens=1000
            )
            
            # Format and structure the analysis
            structured_analysis = {
                "thread_id": thread_id,
                "type": analysis_type,
                "timestamp": self._get_current_timestamp(),
                "insights": analysis.get("insights", []),
                "recommendations": analysis.get("recommendations", []),
                "metrics": analysis.get("metrics", {})
            }
            
            # Cache the analysis
            self._cache_service.set(cache_key, structured_analysis, ttl=1800)  # 30 minutes
            
            # Log the analysis
            self._db_service.save_analysis_result(structured_analysis)
            
            return structured_analysis
            
        except Exception as e:
            self._logger.error(
                f"Error analyzing conversation: {str(e)}",
                exc_info=True,
                extra={"thread_id": thread_id, "analysis_type": analysis_type}
            )
            return {"error": str(e)}
    
    def get_sales_metrics(
        self,
        start_date: str,
        end_date: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Get sales metrics for analysis."""
        try:
            cache_key = f"metrics:{start_date}:{end_date}:{','.join(metrics)}"
            cached_metrics = self._cache_service.get(cache_key)
            
            if cached_metrics:
                return cached_metrics
            
            # Query metrics from database
            metrics_data = self._db_service.query_sales_metrics(
                start_date,
                end_date,
                metrics
            )
            
            # Cache the results
            self._cache_service.set(cache_key, metrics_data, ttl=3600)  # 1 hour
            
            return metrics_data
            
        except Exception as e:
            self._logger.error(f"Error fetching sales metrics: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
