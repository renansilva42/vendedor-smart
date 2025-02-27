# app/chatbot/treinamento.py
from typing import Dict, List, Any
import logging
from .base import BaseChatbot
from config import Config

logger = logging.getLogger("chatbot.treinamento")

class TreinamentoChatbot(BaseChatbot):
    """Chatbot simulador de cliente para treinamento de vendedores."""
    
    def __init__(self):
        super().__init__(
            name="Simulador de Vendas",
            model="gpt-4o",
            assistant_id=Config.ASSISTANT_ID_TREINAMENTO
        )
    
    def get_instructions(self) -> str:
        return (
            "Você é um cliente interessado em comprar uma passagem aérea. "
            "Seu objetivo é treinar um vendedor da companhia aérea em seu processo de vendas. "
            "Simule diferentes perfis de clientes: indeciso, exigente, focado em preço, "
            "focado em conforto, etc. Faça perguntas realistas e apresente objeções comuns. "
            "Varie seu comportamento para criar cenários desafiadores mas realistas. "
            "Não revele que você é uma IA - mantenha o papel de cliente durante toda a interação."
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "log_interaction",
                    "description": "Registra interações do usuário",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thread_id": {"type": "string"},
                            "role": {"type": "string"},
                            "content": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "user_name": {"type": "string"},
                            "chatbot_type": {"type": "string"}
                        },
                        "required": ["thread_id", "role", "content", "timestamp", "user_name"]
                    }
                }
            }
        ]
    
    def _execute_function(self, function_name: str, arguments: Dict, thread_id: str) -> str:
        """Executa funções específicas do chatbot de treinamento."""
        if function_name == "log_interaction":
            return "Log registrado com sucesso"
        else:
            return f"Função {function_name} não implementada"