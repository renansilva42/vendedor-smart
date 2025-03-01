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

class TreinamentoChatbot(BaseChatbot):
    """Refactored Training chatbot with improved architecture."""
    
    def __init__(
        self,
        ai_service: AIServiceInterface,
        db_service: DatabaseServiceInterface,
        cache_service: CacheServiceInterface,
        logger: LoggingServiceInterface
    ):
        super().__init__(
            name="Simulador de Vendas",
            model="gpt-4o",
            ai_service=ai_service,
            db_service=db_service,
            cache_service=cache_service,
            logger=logger,
            assistant_id=Config.ASSISTANT_ID_TREINAMENTO
        )
        self._scenarios = self._load_scenarios()
    
    def get_instructions(self) -> str:
        """Get specialized instructions for the training assistant."""
        return (
            "Você é um simulador avançado de clientes para treinamento de vendedores. "
            "\n\nDiretrizes principais:\n"
            "1. Simule diferentes perfis de clientes de forma realista\n"
            "2. Adapte o comportamento com base no histórico da conversa\n"
            "3. Apresente objeções comuns e desafios reais\n"
            "4. Mantenha consistência no perfil escolhido\n"
            "5. Nunca revele que é uma IA\n"
            "\nPerfis de cliente a simular:\n"
            "- Cliente indeciso que precisa de mais informações\n"
            "- Cliente focado em preço e barganhas\n"
            "- Cliente com urgência na decisão\n"
            "- Cliente técnico que faz muitas perguntas\n"
            "- Cliente que compara com concorrentes\n"
            "\nObjetivo: Criar cenários realistas para treinar:\n"
            "- Habilidades de negociação\n"
            "- Gestão de objeções\n"
            "- Técnicas de fechamento\n"
            "- Comunicação efetiva"
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get specialized tools for the training assistant."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "select_scenario",
                    "description": "Seleciona um cenário de treinamento específico",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "scenario_type": {
                                "type": "string",
                                "enum": [
                                    "price_sensitive",
                                    "technical",
                                    "urgent",
                                    "indecisive",
                                    "competitor_aware"
                                ],
                                "description": "Tipo de cenário a simular"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "medium", "hard"],
                                "description": "Nível de dificuldade do cenário"
                            }
                        },
                        "required": ["scenario_type", "difficulty"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_response",
                    "description": "Avalia a resposta do vendedor",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response_text": {
                                "type": "string",
                                "description": "Resposta do vendedor"
                            },
                            "criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Critérios de avaliação"
                            }
                        },
                        "required": ["response_text", "criteria"]
                    }
                }
            }
        ]
    
    def _load_scenarios(self) -> Dict[str, Any]:
        """Load training scenarios from cache or database."""
        try:
            cache_key = "training_scenarios"
            scenarios = self._cache_service.get(cache_key)
            
            if scenarios:
                self._logger.debug("Retrieved scenarios from cache")
                return scenarios
            
            # If not in cache, load from database
            scenarios = self._db_service.query_scenarios()
            
            if not scenarios:
                # Use default scenarios if none in database
                scenarios = self._get_default_scenarios()
            
            # Cache the scenarios
            self._cache_service.set(cache_key, scenarios, ttl=3600)  # 1 hour
            
            return scenarios
            
        except Exception as e:
            self._logger.error(f"Error loading scenarios: {str(e)}", exc_info=True)
            return self._get_default_scenarios()
    
    def _get_default_scenarios(self) -> Dict[str, Any]:
        """Get default training scenarios."""
        return {
            "price_sensitive": {
                "profile": "Cliente focado em preço",
                "objectives": ["Negociação", "Demonstração de valor"],
                "difficulties": {
                    "easy": {"budget_flexibility": "high", "objection_frequency": "low"},
                    "medium": {"budget_flexibility": "medium", "objection_frequency": "medium"},
                    "hard": {"budget_flexibility": "low", "objection_frequency": "high"}
                }
            },
            "technical": {
                "profile": "Cliente técnico",
                "objectives": ["Conhecimento produto", "Respostas precisas"],
                "difficulties": {
                    "easy": {"technical_depth": "basic", "question_complexity": "low"},
                    "medium": {"technical_depth": "intermediate", "question_complexity": "medium"},
                    "hard": {"technical_depth": "advanced", "question_complexity": "high"}
                }
            },
            # Add more default scenarios...
        }
    
    def select_training_scenario(
        self,
        scenario_type: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Select and configure a training scenario."""
        try:
            if scenario_type not in self._scenarios:
                raise ValueError(f"Invalid scenario type: {scenario_type}")
            
            scenario = self._scenarios[scenario_type]
            difficulty_config = scenario["difficulties"].get(difficulty, "medium")
            
            # Prepare scenario configuration
            config = {
                "type": scenario_type,
                "profile": scenario["profile"],
                "difficulty": difficulty,
                "objectives": scenario["objectives"],
                "settings": difficulty_config
            }
            
            # Store scenario in thread context
            thread_id = self.create_thread()
            self._cache_service.set(
                f"scenario:{thread_id}",
                config,
                ttl=7200  # 2 hours
            )
            
            return {
                "thread_id": thread_id,
                "scenario": config
            }
            
        except Exception as e:
            self._logger.error(f"Error selecting scenario: {str(e)}", exc_info=True)
            raise
    
    def evaluate_response(
        self,
        thread_id: str,
        response: str,
        criteria: List[str]
    ) -> Dict[str, Any]:
        """Evaluate a seller's response in the training scenario."""
        try:
            # Get scenario context
            scenario = self._cache_service.get(f"scenario:{thread_id}")
            if not scenario:
                raise ValueError("No active scenario found for this thread")
            
            # Prepare evaluation context
            context = {
                "scenario": scenario,
                "response": response,
                "criteria": criteria,
                "history": self.get_chat_history(thread_id, limit=5)
            }
            
            # Use AI to evaluate response
            evaluation = self._ai_service.evaluate_response(context)
            
            # Store evaluation
            self._db_service.save_evaluation_result({
                "thread_id": thread_id,
                "scenario_type": scenario["type"],
                "response": response,
                "evaluation": evaluation,
                "timestamp": self._get_current_timestamp()
            })
            
            return evaluation
            
        except Exception as e:
            self._logger.error(
                f"Error evaluating response: {str(e)}",
                exc_info=True,
                extra={"thread_id": thread_id}
            )
            raise
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
