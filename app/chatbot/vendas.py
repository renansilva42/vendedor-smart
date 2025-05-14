from typing import Dict, List, Any, Optional
import json
import logging
import re
from datetime import datetime
from .base import BaseChatbot, supabase, client  # Import client from base.py
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
            "Use a função query_whatsapp_messages para acessar histórico de conversas do WhatsApp "
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
                            "sender_name": {"type": "string", "description": "Nome do remetente"},
                            "content": {"type": "string", "description": "Conteúdo da mensagem"},
                            "start_date": {"type": "string", "format": "date", "description": "Data inicial (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "format": "date", "description": "Data final (YYYY-MM-DD)"},
                            "limit": {"type": "integer", "default": 10, "description": "Limite de resultados"}
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
                            "thread_id": {"type": "string", "description": "ID da thread"},
                            "role": {"type": "string", "description": "Papel do autor (ex: user, assistant)"},
                            "content": {"type": "string", "description": "Conteúdo da mensagem"},
                            "timestamp": {"type": "string", "description": "Data e hora da interação"},
                            "user_name": {"type": "string", "description": "Nome do usuário"},
                            "chatbot_type": {"type": "string", "description": "Tipo do chatbot"}
                        },
                        "required": ["thread_id", "role", "content", "timestamp", "user_name"]
                    }
                }
            }
        ]

    def _execute_function(self, function_name: str, arguments: Dict, thread_id: str) -> str:
        try:
            if function_name == "query_whatsapp_messages":
                return self._query_whatsapp_data(arguments)
            elif function_name == "log_interaction":
                return self._log_interaction_function(arguments)
            logger.warning(f"Função {function_name} não reconhecida")
            return json.dumps({"status": "error", "message": f"Função {function_name} não implementada"})
        except Exception as e:
            logger.error(f"Erro ao executar função {function_name}: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

    def _query_whatsapp_data(self, params: Dict) -> str:
        try:
            query = supabase.table("whatsapp_messages").select("*")
            if sender_name := params.get("sender_name"):
                query = query.ilike("sender_name", f"%{sender_name}%")
            if content := params.get("content"):
                query = query.ilike("content", f"%{content}%")
            if start_date := params.get("start_date"):
                if end_date := params.get("end_date"):
                    query = query.gte("timestamp", start_date).lte("timestamp", end_date)
                else:
                    query = query.gte("timestamp", start_date)
            query = query.order("timestamp", desc=True).limit(params.get("limit", 10))
            result = query.execute()
            formatted_messages = [
                {
                    "sender": msg.get("sender_name", "Desconhecido"),
                    "message": msg.get("content", ""),
                    "date": msg.get("timestamp", "")
                }
                for msg in result.data
            ]
            logger.info(f"Consulta Supabase retornou: {len(formatted_messages)} itens")
            return json.dumps({
                "status": "success",
                "data": formatted_messages,
                "count": len(formatted_messages),
                "query_params": params
            }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro na consulta ao Supabase: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e),
                "query_params": params
            }, ensure_ascii=False)

    def _log_interaction_function(self, params: Dict) -> str:
        try:
            logger.info(f"Interação registrada: {params}")
            return json.dumps({"status": "success", "message": "Log registrado com sucesso"})
        except Exception as e:
            logger.error(f"Erro ao registrar log: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

    def _format_response(self, messages: List[Any], thread_id: str) -> Dict[str, Any]:
        try:
            assistant_messages = [msg for msg in messages if msg.role == "assistant"]
            if not assistant_messages:
                logger.warning(f"Nenhuma mensagem do assistente encontrada na thread {thread_id}")
                return {"response": "Desculpe, não consegui gerar uma resposta.", "thread_id": thread_id}
            parts = []
            for msg in assistant_messages:
                if isinstance(msg.content, list):
                    for content_block in msg.content:
                        if hasattr(content_block, "text") and hasattr(content_block.text, "value"):
                            parts.append(content_block.text.value)
                        else:
                            parts.append(str(content_block))
                else:
                    parts.append(str(msg.content))
            full_response = " ".join(parts).strip()
            if not full_response:
                logger.warning(f"Resposta vazia após formatação na thread {thread_id}")
                return {"response": "Resposta vazia gerada.", "thread_id": thread_id}
            return {"response": full_response, "thread_id": thread_id}
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}", exc_info=True)
            return {"response": "Erro ao formatar a resposta.", "thread_id": thread_id}

    def _handle_required_actions(self, thread_id: str, run_id: str, run_status: Any) -> None:
        logger.info(f"Handling required actions for run {run_id} in thread {thread_id} with status {run_status.status}")
        try:
            if not run_status.required_action or not run_status.required_action.submit_tool_outputs:
                logger.warning(f"No tool outputs required for run {run_id}")
                return
            tool_outputs = []
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                logger.info(f"Executing function {function_name} with arguments {arguments}")
                output = self._execute_function(function_name, arguments, thread_id)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            logger.info(f"Submitting tool outputs for run {run_id}: {tool_outputs}")
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )
            logger.info(f"Tool outputs submitted successfully for run {run_id}")
        except Exception as e:
            logger.error(f"Error handling required actions for run {run_id}: {str(e)}", exc_info=True)

    def extract_name(self, message: str) -> str:
        if not message:
            return ""
        match = re.search(r"meu nome é ([A-Za-zÀ-ÿ\s]+)", message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            logger.info(f"Nome extraído da mensagem: {name}")
            return name
        return ""