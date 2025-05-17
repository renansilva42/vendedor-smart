# app/chatbot/treinamento.py
from typing import Dict, List, Any, Optional
import logging
from .base import BaseChatbot
from config import Config

logger = logging.getLogger("chatbot.treinamento")

class TreinamentoChatbot(BaseChatbot):
    """Chatbot simulador de cliente para treinamento de vendedores."""
    
    def __init__(self):
        super().__init__(
            name="IA Treinamento de Vendas",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_user_name",
                    "description": "Extrai o nome do usuário da mensagem quando ele se apresenta",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_name": {"type": "string", "description": "Nome do usuário extraído da mensagem"}
                        },
                        "required": ["user_name"]
                    }
                }
            }
        ]
    
    def _execute_function(self, function_name: str, arguments: Dict, thread_id: str) -> str:
        """Executa funções específicas do chatbot de treinamento."""
        if function_name == "log_interaction":
            return "Log registrado com sucesso"
        elif function_name == "extract_user_name":
            return "Nome do usuário extraído com sucesso"
        else:
            return f"Função {function_name} não implementada"
            
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """
        Envia uma mensagem para o assistente e retorna a resposta.
        """
        try:
            response = super().send_message(thread_id, message)
            
            # Se o retorno contém tool_calls, processa-os
            if 'tool_calls' in response and response['tool_calls']:
                for tool_call in response['tool_calls']:
                    if tool_call.get('function', {}).get('name') == 'extract_user_name':
                        # Extrair o nome do usuário se fornecido na ferramenta
                        try:
                            user_name = tool_call.get('function', {}).get('arguments', {}).get('user_name', '')
                            if user_name and user_name != "Usuário Anônimo":
                                # Incluir o nome extraído na resposta para atualizações posteriores
                                response['user_name'] = user_name
                        except Exception as e:
                            logger.error(f"Erro ao extrair nome do usuário: {str(e)}")
            
            # Garantir que todas as respostas do chatbot de treinamento tenham o nome "IA Treinamento de Vendas"
            if 'response' in response:
                return {
                    'response': response['response'],
                    'user_name': response.get('user_name', ''),
                    'assistant_name': 'IA Treinamento de Vendas'
                }
            
            # Adicionar assistant_name mesmo quando não há 'response' no retorno
            response['assistant_name'] = 'IA Treinamento de Vendas'
            return response
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o chatbot de treinamento: {str(e)}")
            return {'error': str(e), 'assistant_name': 'IA Treinamento de Vendas'}
