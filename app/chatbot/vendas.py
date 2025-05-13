# app/chatbot/vendas.py
from typing import Dict, List, Any
import json
import logging
from .base import BaseChatbot
from config import Config

logger = logging.getLogger("chatbot.vendas")

class VendasChatbot(BaseChatbot):
    """Chatbot especialista em vendas para mentoria."""
    
    def __init__(self):
        super().__init__(
            name="Assistente de Vendas (Mentor)",
            model="gpt-4o",
            assistant_id=Config.ASSISTANT_ID_VENDAS
        )
    
    def get_instructions(self) -> str:
        return (
            "Você é um especialista em vendas, atuando como mentor para vendedores. "
            "Seu objetivo é ajudar a melhorar as técnicas de vendas, oferecer dicas "
            "e analisar conversas anteriores para identificar pontos de melhoria. "
            "Use query_whatsapp_messages para acessar histórico de conversas do WhatsApp "
            "quando o usuário mencionar 'histórico', 'mensagens anteriores', 'consultar conversas' "
            "ou termos similares. Seja sempre construtivo e focado em resultados."
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_whatsapp_messages",
                    "description": "Consulta históricos do WhatsApp com filtros por remetente, conteúdo e datas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sender_name": {"type": "string"},
                            "content": {"type": "string"},
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"},
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            },
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
        """Executa funções específicas do chatbot de vendas."""
        if function_name == "query_whatsapp_messages":
            return self._query_whatsapp_data(arguments)
        elif function_name == "log_interaction":
            return self._log_interaction_function(arguments)
        else:
            return f"Função {function_name} não implementada"
    
    def _query_whatsapp_data(self, params: Dict) -> str:
        """Busca registros de WhatsApp aplicando filtros e ordenação."""
        try:
            from .base import supabase
            
            query = supabase.table('whatsapp_messages').select('*')
            if params.get('sender_name'):
                query = query.ilike('sender_name', f"%{params['sender_name']}%")
            if params.get('content'):
                query = query.ilike('content', f"%{params['content']}%")
            if params.get('start_date') and params.get('end_date'):
                query = query.gte('timestamp', params['start_date']).lte('timestamp', params['end_date'])
            query = query.order('timestamp', desc=True).limit(params.get('limit', 10))
            result = query.execute()
            logger.info(f"Consulta Supabase retornou: {len(result.data)} itens")
            
            # Formatar os resultados para melhor legibilidade
            formatted_messages = []
            for msg in result.data:
                formatted_messages.append({
                    "sender": msg.get("sender_name", "Desconhecido"),
                    "message": msg.get("content", ""),
                    "date": msg.get("timestamp", "")
                })
            
            return json.dumps({
                "status": "success",
                "data": formatted_messages,
                "count": len(formatted_messages),
                "query_params": params
            })
        except Exception as e:
            logger.error(f"Erro na consulta ao Supabase: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e),
                "query_params": params
            })
    
    def _log_interaction_function(self, params: Dict) -> str:
        """Função específica para logging chamada pelo assistente."""
        try:
            # Implementação simplificada - já temos logging automático
            logger.info(f"Log solicitado pelo assistente: {params}")
            return "Log registrado com sucesso"
        except Exception as e:
            logger.error(f"Erro ao registrar logs: {str(e)}", exc_info=True)
            return f"Erro no registro: {str(e)}"

    def _format_response(self, messages: List[Dict[str, Any]], thread_id: str) -> Dict[str, Any]:
        """Formata a resposta do chatbot a partir das mensagens da thread."""
        try:
            # Filtrar mensagens do assistente
            assistant_messages = [msg for msg in messages if msg.role == "assistant"]
            if not assistant_messages:
                return {"response": "Desculpe, não consegui gerar uma resposta.", "thread_id": thread_id}
            
            # Concatenar conteúdos das mensagens do assistente, convertendo listas to strings if needed
            parts = []
            for msg in assistant_messages:
                content = msg.content
                if isinstance(content, list):
                    # Detect if list contains TextContentBlock objects with text.value
                    if content and hasattr(content[0], "text") and hasattr(content[0].text, "value"):
                        parts.append(" ".join(str(c.text.value) for c in content))
                    else:
                        parts.append(" ".join(str(c) for c in content))
                elif isinstance(content, str):
                    parts.append(content)
                else:
                    parts.append(str(content))
            full_response = " ".join(parts)
            
            return {"response": full_response.strip(), "thread_id": thread_id}
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}", exc_info=True)
            return {"response": "Erro ao formatar a resposta.", "thread_id": thread_id}
