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
from app.models import TIMEZONE

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
        """
        Inicializa um novo chatbot.
        
        Args:
            name (str): Nome do chatbot
            model (str): Modelo GPT a ser usado
            assistant_id (Optional[str]): ID do assistente OpenAI existente
        """
        if not name:
            raise ValueError("Nome do chatbot é obrigatório")
            
        self.name = name
        self.model = model
        self.assistant_id = assistant_id
        self.assistant = None
        self._name_cache = {}
        
        try:
            self.initialize_assistant()
        except Exception as e:
            logger.error(f"Falha na inicialização do chatbot {name}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Não foi possível inicializar o chatbot {name}")

    def _initialize_assistant(self) -> None:
        """Inicializa ou recupera o assistente da OpenAI com retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.assistant_id:
                    logger.info(f"Criando novo assistente para {self.name}")
                    self._create_assistant()
                    break
                else:
                    self.assistant = client.beta.assistants.retrieve(self.assistant_id)
                    logger.info(f"Assistente recuperado: {self.name} (ID: {self.assistant_id})")
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Todas as tentativas de inicialização falharam para {self.name}")
                    raise RuntimeError(f"Falha na inicialização do chatbot {self.name}")
                logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                time.sleep(2 ** attempt)  # Backoff exponencial


    def initialize_assistant(self) -> None:
        """Wrapper público para _initialize_assistant para evitar erros de atributo."""
        self._initialize_assistant()

    def initialize_assistant(self) -> None:
        """Wrapper público para _initialize_assistant para evitar erros de atributo."""
        self._initialize_assistant()

    def _create_assistant(self) -> None:
        """Cria um novo assistente com validações."""
        try:
            instructions = self.get_instructions()
            tools = self.get_tools()
            
            if not instructions:
                raise ValueError("Instruções não podem estar vazias")
                
            self.assistant = client.beta.assistants.create(
                name=self.name,
                instructions=instructions,
                model=self.model,
                tools=tools
            )
            self.assistant_id = self.assistant.id
            logger.info(f"Novo assistente criado: {self.name} (ID: {self.assistant_id})")
            
        except Exception as e:
            logger.error(f"Erro ao criar assistente {self.name}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Falha na criação do assistente: {str(e)}")

    @lru_cache(maxsize=100)
    def create_thread(self) -> str:
        """Cria uma nova thread com cache e retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                thread = client.beta.threads.create()
                logger.info(f"Nova thread criada: {thread.id}")
                return thread.id
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error("Todas as tentativas de criar thread falharam")
                    raise RuntimeError("Não foi possível criar uma nova thread")
                logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                time.sleep(2 ** attempt)

    def _get_active_run(self, thread_id: str) -> Optional[Any]:
        """Retorna o run ativo (queued ou in_progress) para o thread_id, ou None se não houver."""
        try:
            runs = client.beta.threads.runs.list(thread_id=thread_id)
            for run in runs.data:
                if run.status in ['queued', 'in_progress']:
                    return run
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar runs ativos para thread {thread_id}: {str(e)}", exc_info=True)
            return None

    def send_message(self, thread_id: str, message: str, user_name: str = "Usuário") -> Dict[str, Any]:
        """Envia mensagem e processa resposta com retry."""
        if not thread_id or not message:
            raise ValueError("thread_id e message são obrigatórios")

        try:
            # Verificar se existe algum run ativo (queued ou in_progress)
            active_run = self._get_active_run(thread_id)
            if active_run:
                logger.info(f"Run ativo encontrado (ID: {active_run.id}), aguardando conclusão antes de enviar nova mensagem.")
                # Esperar o run ativo completar
                result = self._process_run(thread_id, active_run.id)
                if "response" in result:
                    self._log_interaction(thread_id, "assistant", result["response"], self.name)
                # Retornar resposta do run ativo sem enviar nova mensagem
                return {
                    "response": "Ainda processando sua mensagem anterior, por favor aguarde.",
                    "thread_id": thread_id,
                    "active_run_id": active_run.id
                }

            # Registrar mensagem do usuário
            self._log_interaction(thread_id, "user", message, user_name)

            # Enviar mensagem
            response = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            # Criar e processar run
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Processar run e obter resposta
            result = self._process_run(thread_id, run.id)

            # Registrar resposta do assistente
            if "response" in result:
                self._log_interaction(thread_id, "assistant", result["response"], self.name)

            return result

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem.",
                "thread_id": thread_id,
                "error": str(e)
            }
    def _process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Processa a execução do run com timeout e tratamento de estados."""
        max_attempts = 30
        attempts = 0

        while attempts < max_attempts:
            try:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )

                if run_status.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    return self._format_response(messages, thread_id)

                elif run_status.status == 'failed':
                    error_msg = getattr(run_status, 'last_error', {'message': 'Erro desconhecido'}).message
                    logger.error(f"Run falhou: {error_msg}")
                    return {"response": f"Desculpe, ocorreu um erro: {error_msg}", "thread_id": thread_id}

                elif run_status.status == 'requires_action':
                    self._handle_required_actions(thread_id, run_id, run_status)

                elif run_status.status not in ['queued', 'in_progress']:
                    logger.warning(f"Status inesperado do run: {run_status.status}")

            except Exception as e:
                logger.error(f"Erro ao verificar status do run: {str(e)}", exc_info=True)
                return {"response": "Erro ao processar sua mensagem", "thread_id": thread_id}

            attempts += 1
            time.sleep(1)

        return {"response": "Tempo limite excedido", "thread_id": thread_id}
class BaseChatbot:
    """Classe base para todos os chatbots do sistema."""

    def __init__(self, name: str, model: str = "gpt-4o", assistant_id: Optional[str] = None):
        """
        Inicializa um novo chatbot.

        Args:
            name (str): Nome do chatbot
            model (str): Modelo GPT a ser usado
            assistant_id (Optional[str]): ID do assistente OpenAI existente
        """
        if not name:
            raise ValueError("Nome do chatbot é obrigatório")

        self.name = name
        self.model = model
        self.assistant_id = assistant_id
        self.assistant = None
        self._name_cache = {}

        try:
            self._initialize_assistant()
        except Exception as e:
            logger.error(f"Todas as tentativas de inicialização falharam para {self.name}")
            raise RuntimeError("Não foi possível criar uma nova thread")
        logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
        time.sleep(2 ** attempt)
