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
        self._name_cache = {}  # Cache para armazenar nomes de usuários por thread_id

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
            },
            {
                "type": "function",
                "function": {
                    "name": "update_user_name",
                    "description": "Atualiza o nome do usuário no banco de dados",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thread_id": {"type": "string", "description": "ID da thread"},
                            "user_name": {"type": "string", "description": "Nome do usuário"}
                        },
                        "required": ["thread_id", "user_name"]
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
            elif function_name == "update_user_name":
                return self._update_user_name(arguments)
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
            
    def _update_user_name(self, params: Dict) -> str:
        try:
            thread_id = params.get("thread_id")
            user_name = params.get("user_name", "").strip()
            
            if not thread_id:
                logger.warning("Thread ID não fornecido para atualização de nome")
                return json.dumps({
                    "status": "error",
                    "message": "thread_id é obrigatório"
                })
            
            # Validar o nome do usuário
            if not user_name or user_name == "Usuário Anônimo" or len(user_name) < 2:
                logger.warning(f"Nome de usuário inválido: {user_name}")
                return json.dumps({
                    "status": "error",
                    "message": "Nome de usuário inválido"
                })
            
            # Verificar se o nome contém apenas caracteres válidos (letras e espaços)
            if not re.match(r'^[A-Za-zÀ-ÿ\s]{2,30}$', user_name):
                logger.warning(f"Nome de usuário contém caracteres inválidos: {user_name}")
                return json.dumps({
                    "status": "error",
                    "message": "Nome de usuário contém caracteres inválidos"
                })
            
            # Salva o nome do usuário
            self.save_user_name(thread_id, user_name)
            
            return json.dumps({
                "status": "success",
                "message": f"Nome do usuário atualizado para: {user_name}",
                "thread_id": thread_id,
                "user_name": user_name
            })
        except Exception as e:
            logger.error(f"Erro ao atualizar nome do usuário: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def _format_response(self, messages: List[Any], thread_id: str) -> Dict[str, Any]:
        try:
            # Recuperar o nome do usuário
            user_name = self.get_user_name(thread_id)
            
            # Check for user messages to extract name
            user_messages = [msg for msg in messages if msg.role == "user"]
            for msg in user_messages:
                if isinstance(msg.content, list):
                    for content_block in msg.content:
                        if hasattr(content_block, "text") and hasattr(content_block.text, "value"):
                            extracted_name = self.extract_name(content_block.text.value)
                            if extracted_name:
                                self.save_user_name(thread_id, extracted_name)
                                user_name = extracted_name
                                break
                else:
                    extracted_name = self.extract_name(str(msg.content))
                    if extracted_name:
                        self.save_user_name(thread_id, extracted_name)
                        user_name = extracted_name
                        break
                        
            assistant_messages = [msg for msg in messages if msg.role == "assistant"]
            if not assistant_messages:
                logger.warning(f"Nenhuma mensagem do assistente encontrada na thread {thread_id}")
                return {
                    "response": "Desculpe, não consegui gerar uma resposta.", 
                    "thread_id": thread_id,
                    "user_name": user_name
                }
                
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
                return {
                    "response": "Resposta vazia gerada.", 
                    "thread_id": thread_id,
                    "user_name": user_name
                }
                
            # Incluir o nome do usuário na resposta
            return {
                "response": full_response, 
                "thread_id": thread_id,
                "user_name": user_name
            }
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}", exc_info=True)
            return {
                "response": "Erro ao formatar a resposta.", 
                "thread_id": thread_id,
                "user_name": "Usuário Anônimo"
            }

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
                
                # Adicionar validação extra para o update_user_name
                if function_name == "update_user_name":
                    if "user_name" in arguments:
                        user_name = arguments.get("user_name", "").strip()
                        # Verificar se o nome está no formato esperado
                        if not re.match(r'^[A-Za-zÀ-ÿ\s]{2,30}$', user_name):
                            logger.warning(f"Nome de usuário inválido: {user_name}")
                            arguments["user_name"] = ""  # Limpar nome inválido
                
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
        """
        Extrai o nome do usuário da mensagem usando padrões específicos.
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Nome extraído ou string vazia se nenhum nome for encontrado
        """
        if not message:
            return ""
        
        # Lista de padrões específicos para identificar nomes
        patterns = [
            r"meu nome[^\w]* (?:é|eh)[^\w]* ([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)",  # "Meu nome é João Silva"
            r"me chamo[^\w]* ([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)",    # "Me chamo João Silva"
            r"(?:pode[^\w]* )?me chamar de[^\w]* ([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)",  # "Pode me chamar de João"
            r"meu nome é ([A-Za-zÀ-ÿ]+)",  # "Meu nome é João"
            r"sou o ([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)",  # "Sou o João Silva"
            r"sou a ([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?)",  # "Sou a Maria Silva"
            r"([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)?) é meu nome",  # "João Silva é meu nome"
        ]
        
        # Lista de palavras para filtrar falsos positivos
        common_words = [
            "sim", "não", "nao", "ok", "oi", "olá", "ola", "bom", "boa", "dia", "tarde", "noite",
            "obrigado", "obrigada", "ajuda", "claro", "todos", "todas", "porque", "como",
            "quero", "queria", "vamos", "agora", "hoje", "amanhã", "amanha", "ontem",
            "vendedor", "cliente", "pessoa", "gente", "pessoal", "equipe", "empresa"
        ]
        
        # Tenta cada padrão até encontrar um match
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Limpa o nome removendo pontuações no final
                name = re.sub(r'[.,;:!?"]$', '', name)
                
                # Verifica se o nome obtido não é uma palavra comum
                if name.lower() in common_words:
                    logger.debug(f"Nome extraído '{name}' é uma palavra comum, ignorando")
                    continue
                    
                # Verifica comprimento válido (entre 2 e 30 caracteres)
                if 2 <= len(name) <= 30:
                    logger.info(f"Nome extraído da mensagem: {name}")
                    return name
        
        return ""
        
    def get_user_name(self, thread_id: str) -> str:
        """
        Recupera o nome do usuário do banco de dados ou cache.
        
        Args:
            thread_id: ID da thread
            
        Returns:
            Nome do usuário ou "Usuário Anônimo" se não encontrado
        """
        # Verificar se já temos o nome em cache
        if thread_id in self._name_cache:
            return self._name_cache[thread_id]
        
        try:
            # Buscar primeiro na tabela de perfis (mais confiável)
            result = supabase.table("perfis_usuario").select("user_name").eq("thread_id", thread_id).execute()
            if result.data and len(result.data) > 0 and result.data[0].get("user_name"):
                user_name = result.data[0].get("user_name")
                # Armazenar em cache
                self._name_cache[thread_id] = user_name
                return user_name
                
            # Se não encontrar, buscar nas mensagens
            result = supabase.table("mensagens_chatbot").select("user_name").eq("thread_id", thread_id).limit(1).execute()
            if result.data and len(result.data) > 0 and result.data[0].get("user_name"):
                user_name = result.data[0].get("user_name")
                if user_name != "Usuário Anônimo":
                    # Armazenar em cache
                    self._name_cache[thread_id] = user_name
                    return user_name
        except Exception as e:
            logger.error(f"Erro ao recuperar nome do usuário: {str(e)}", exc_info=True)
        
        # Valor padrão se não encontrar
        return "Usuário Anônimo"
        
    def save_user_name(self, thread_id: str, user_name: str) -> None:
        """
        Salva o nome do usuário no banco de dados Supabase.
        
        Args:
            thread_id: ID da thread atual
            user_name: Nome do usuário a ser salvo
        """
        try:
            if not user_name or not thread_id:
                logger.debug(f"Thread ID ou nome de usuário vazio, não será salvo: {user_name}")
                return
                
            # Verificações adicionais para evitar nomes inválidos
            if user_name == "Usuário Anônimo" or len(user_name) < 2:
                logger.debug(f"Nome de usuário inválido ou padrão, não será salvo: {user_name}")
                return
                
            # Armazenar o nome do usuário em cache para uso futuro nesta sessão
            self._name_cache[thread_id] = user_name
                
            logger.info(f"Salvando nome do usuário na tabela mensagens_chatbot: {user_name}")
            
            # Atualizar todas as mensagens para este thread
            result = supabase.table("mensagens_chatbot").update(
                {"user_name": user_name}
            ).eq("thread_id", thread_id).execute()
            
            affected_rows = len(result.data) if hasattr(result, 'data') else 0
            logger.info(f"Nome do usuário salvo com sucesso. Registros atualizados: {affected_rows}")
            
            # Armazenar também na tabela de perfis de usuário para persistência
            try:
                # Verificar se já existe um perfil para este thread
                profile_check = supabase.table("perfis_usuario").select("*").eq("thread_id", thread_id).execute()
                
                if profile_check.data and len(profile_check.data) > 0:
                    # Atualizar perfil existente
                    supabase.table("perfis_usuario").update(
                        {"user_name": user_name, "updated_at": datetime.now().isoformat()}
                    ).eq("thread_id", thread_id).execute()
                else:
                    # Criar novo perfil
                    supabase.table("perfis_usuario").insert(
                        {"thread_id": thread_id, "user_name": user_name, "created_at": datetime.now().isoformat()}
                    ).execute()
                    
                logger.info(f"Perfil do usuário atualizado com o nome: {user_name}")
            except Exception as e:
                logger.error(f"Erro ao atualizar perfil do usuário: {str(e)}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Erro ao salvar nome do usuário no Supabase: {str(e)}", exc_info=True)
            
    def send_message(self, thread_id: str, message: str, user_name: str = "Usuário Anônimo") -> Dict[str, Any]:
        """
        Envia uma mensagem para o chatbot e processa a extração de nome do usuário.
        
        Args:
            thread_id: ID da thread
            message: Conteúdo da mensagem
            user_name: Nome do usuário (padrão: "Usuário Anônimo")
            
        Returns:
            Dicionário contendo a resposta do chatbot
        """
        # Obter o nome do usuário usando o método get_user_name
        user_name = self.get_user_name(thread_id)
        logger.info(f"Nome do usuário recuperado: {user_name}")
        
        # Tenta extrair o nome do usuário da mensagem atual
        extracted_name = self.extract_name(message)
        
        # Se encontrou um nome na mensagem, atualiza o user_name
        if extracted_name:
            # Verificar se o nome extraído é diferente do nome atual
          if extracted_name != user_name:
                user_name = extracted_name
                # Atualizar o cache
                self._name_cache[thread_id] = user_name
                # Salva o nome do usuário no banco de dados
                self.save_user_name(thread_id, user_name)
                logger.info(f"Nome do usuário atualizado para: {user_name}")
        
        # Chama o método da classe pai para processar a mensagem, usando o nome correto
        return super().send_message(thread_id, message, user_name)
