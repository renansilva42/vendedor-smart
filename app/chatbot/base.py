# app/chatbot/base.py (refatorado)
from openai import OpenAI
from config import Config
import time
import json
from typing import Optional, List, Dict, Any, Union, Callable
from supabase import create_client
import logging
import datetime
from functools import lru_cache

client = OpenAI(api_key=Config.OPENAI_API_KEY)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Configuração de logging centralizada
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class BaseChatbot:
    """Classe base para todos os chatbots do sistema."""
    
    def __init__(self, name: str, model: str = "gpt-4o", assistant_id: Optional[str] = None):
        self.name = name
        self.model = model
        self.assistant_id = assistant_id
        self._initialize_assistant()
        
    def _initialize_assistant(self) -> None:
        """Inicializa ou recupera o assistente da OpenAI."""
        if not self.assistant_id:
            logger.warning(f"Nenhum ID de assistente fornecido para {self.name}. Criando novo.")
            self._create_assistant()
        else:
            try:
                self.assistant = client.beta.assistants.retrieve(self.assistant_id)
                logger.info(f"Assistente recuperado: {self.name} (ID: {self.assistant_id})")
            except Exception as e:
                logger.error(f"Erro ao recuperar assistente {self.name}: {str(e)}")
                self._create_assistant()
    
    def _create_assistant(self) -> None:
        """Cria um novo assistente com as configurações padrão."""
        try:
            self.assistant = client.beta.assistants.create(
                name=self.name,
                instructions=self.get_instructions(),
                model=self.model,
                tools=self.get_tools()
            )
            self.assistant_id = self.assistant.id
            logger.info(f"Novo assistente criado: {self.name} (ID: {self.assistant_id})")
        except Exception as e:
            logger.error(f"Erro ao criar assistente {self.name}: {str(e)}")
            raise RuntimeError(f"Não foi possível criar o assistente {self.name}: {str(e)}")
    
    def get_instructions(self) -> str:
        if self.chatbot_type == 'atual' or self.chatbot_type == 'novo':
            return (
                "Você é um assistente especializado em vendas. "
                "Na primeira interação, sempre pergunte educadamente o nome do usuário. "
                "Exemplo: 'Olá! Sou seu assistente de vendas. Como posso chamá-lo(a)?' "
                "Depois de obter o nome, use-o nas interações seguintes para personalizar o atendimento."
                # resto das instruções...
            )
    # outras instruções para outros tipos de chatbot...
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Retorna as ferramentas disponíveis para este chatbot."""
        return []
    
    @lru_cache(maxsize=100)
    def create_thread(self) -> str:
        """Cria uma nova thread de conversa com cache para evitar duplicações."""
        try:
            thread = client.beta.threads.create()
            logger.info(f"Nova thread criada: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Erro ao criar thread: {str(e)}")
            raise RuntimeError(f"Não foi possível criar uma nova thread: {str(e)}")
    
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Envia mensagem para o thread com tratamento de erros aprimorado."""
        try:
            return client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            # Tentar novamente com backoff exponencial
            for attempt in range(3):
                try:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    return client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=message
                    )
                except Exception as retry_e:
                    logger.error(f"Tentativa {attempt+1} falhou: {str(retry_e)}")
            
            # Retornar resposta de fallback após falhas
            return {"id": None, "content": "Erro de comunicação com o assistente."}
    
    def _process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Processa a execução da thread, incluindo chamadas de ferramentas."""
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                logger.info(f"Status do run {run_id}: {run_status.status}")
                
                if run_status.status == 'completed':
                    msgs = client.beta.threads.messages.list(thread_id=thread_id)
                    return self._format_response(msgs, thread_id)
                
                elif run_status.status == 'failed':
                    error_msg = run_status.last_error.message if hasattr(run_status, 'last_error') else "Erro desconhecido"
                    logger.error(f"Run falhou: {error_msg}")
                    return {"response": f"Desculpe, ocorreu um erro: {error_msg}", "thread_id": thread_id}
                
                elif run_status.status == 'requires_action':
                    self._handle_required_actions(thread_id, run_id, run_status)
                
                elif run_status.status in ['queued', 'in_progress']:
                    # Continuar esperando
                    pass
                
                else:
                    logger.warning(f"Status desconhecido do run: {run_status.status}")
            
            except Exception as e:
                logger.error(f"Erro ao verificar status do run: {str(e)}", exc_info=True)
                return {"response": f"Erro ao processar sua mensagem: {str(e)}", "thread_id": thread_id}
            
            time.sleep(1)
        
        # Se chegou aqui, atingiu o limite de tentativas
        logger.error(f"Tempo limite excedido para o run {run_id}")
        return {"response": "Desculpe, o processamento da sua mensagem demorou muito tempo. Por favor, tente novamente.", "thread_id": thread_id}
    
    def _handle_required_actions(self, thread_id: str, run_id: str, run_status: Any) -> None:
        """Processa ações requeridas pelo assistente."""
        outputs = []
        for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            output = self._execute_function(fn_name, args, thread_id)
            outputs.append({
                "tool_call_id": tool_call.id,
                "output": output
            })

        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=outputs
        )
        logger.info(f"Outputs de ferramentas enviados para o run {run_id}")
    
    def _execute_function(self, function_name: str, arguments: Dict, thread_id: str) -> str:
        """Executa a função solicitada pelo assistente."""
        logger.info(f"Executando função {function_name} com argumentos: {arguments}")
        try:
            # Implementar na classe derivada
            return "Função não implementada"
        except Exception as e:
            logger.error(f"Erro na execução da função {function_name}: {str(e)}", exc_info=True)
            return f"Erro na execução: {str(e)}"
    
    def _format_response(self, messages, thread_id: str) -> Dict[str, Any]:
        """Formata a resposta do assistente."""
        try:
            if not messages.data:
                logger.warning(f"Nenhuma mensagem encontrada para thread_id: {thread_id}")
                return {
                    "response": "Desculpe, não foi possível gerar uma resposta.",
                    "thread_id": thread_id,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            last_message = messages.data[0].content[0].text.value
            iso_timestamp = datetime.datetime.now().isoformat()
            
            return {
                "response": last_message,
                "thread_id": thread_id,
                "timestamp": iso_timestamp
            }
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar a resposta.",
                "thread_id": thread_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _log_interaction(self, thread_id: str, role: str, content: str, user_name: str) -> None:
        """Registra a interação no banco de dados."""
        try:
            message_data = {
                "thread_id": thread_id,
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.now().isoformat(),
                "user_name": user_name,
                "chatbot_type": self.name
            }
            supabase.table('mensagens_chatbot').insert(message_data).execute()
            logger.debug(f"Interação registrada: {role} - {thread_id}")
        except Exception as e:
            logger.error(f"Erro ao registrar interação: {str(e)}", exc_info=True)
    
    def extract_name(self, message: str) -> Optional[str]:
        """Extrai o nome do usuário da mensagem."""
        try:
            # Implementação simplificada - usar regex ou LLM para extração mais precisa
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["sou", "chamo", "nome"]:
                    if i + 1 < len(words):
                        return words[i + 1].strip(",.:;!?")
            return None
        except Exception as e:
            logger.error(f"Erro na extração de nome: {str(e)}", exc_info=True)
            return None