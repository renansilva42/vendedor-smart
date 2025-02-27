# app/chatbot.py
from openai import OpenAI
from config import Config
import time
import json
from typing import Optional, List, Dict
from supabase import create_client
import logging
import datetime

client = OpenAI(api_key=Config.OPENAI_API_KEY)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class Chatbot:
    def __init__(self, chatbot_type: str):
        self.manager = ChatbotManager()
        self.chatbot_type = chatbot_type

    def create_thread(self) -> str:
        return self.manager.create_thread()

    def send_message(self, thread_id: str, message: str) -> str:
        resposta = self.manager.process_message(
            chatbot_type=self.chatbot_type,
            user_message=message,
            thread_id=thread_id
        )
        return resposta.get('response', 'Desculpe, não foi possível gerar uma resposta.')

    def extract_name(self, message: str) -> Optional[str]:
        return self.manager.extract_name(message)

    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        return self.manager.generate_summary(messages)

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 30):
        self.manager._wait_for_run_completion(thread_id, run_id, timeout)


class ChatbotManager:
    def __init__(self):
        self.assistants = {}
        self._initialize_assistants()
        self._verify_assistants()  # Nova função para verificar assistentes
        self._verify_supabase_access()

    def _initialize_assistants(self):
        """Cria ou obtém auxiliares, validando ferramentas."""
        assistants_map = {
            "atual": {
                "name": "Assistente de Vendas (Mentor)",
                "functions": ["query_whatsapp_messages", "log_interaction"],
                "model": "gpt-4o",  # Atualizado para um modelo mais estável
                "instructions": (
                    "Você é um especialista em vendas. Use query_whatsapp_messages para acessar "
                    "histórico de conversas do WhatsApp. Sempre que o usuário mencionar 'histórico', "
                    "'mensagens anteriores' ou pedir para 'consultar conversas', ou algo similar a isso, utilize a função."
                ),
                "id": Config.ASSISTANT_ID_VENDAS
            },
            "novo": {
                "name": "Simulador de Vendas",
                "functions": ["log_interaction"],
                "model": "gpt-4o",  # Atualizado para um modelo mais estável
                "instructions": "Você é um cliente interessado em comprar uma passagem aérea, com o objetivo de treinar um vendedor da companhia aérea em seu processo de vendas.",
                "id": Config.ASSISTANT_ID_TREINAMENTO
            },
            "whatsapp": {
                "name": "Assistente WhatsApp",
                "functions": [],
                "model": "gpt-4o",  # Atualizado para um modelo mais estável
                "instructions": "Você é especialista em análise de conversas do WhatsApp.",
                "id": Config.ASSISTANT_ID_WHATSAPP
            }
        }

        for key, params in assistants_map.items():
            assistant = self._get_or_create_assistant(params)
            self._validate_assistant_tools(assistant, params["functions"])
            self.assistants[key] = assistant

    def _verify_assistants(self):
        """Verifica se os assistentes estão funcionando corretamente."""
        for key, assistant in self.assistants.items():
            try:
                # Tenta obter informações do assistente
                assistant_info = client.beta.assistants.retrieve(assistant.id)
                logger.info(f"Assistente {key} verificado: {assistant_info.name} (ID: {assistant_info.id})")
            except Exception as e:
                logger.error(f"Erro ao verificar assistente {key}: {str(e)}")
                raise RuntimeError(f"Assistente {key} não está disponível: {str(e)}")
        
        logger.info("Todos os assistentes verificados com sucesso")

    def _get_or_create_assistant(self, params: Dict):
        """Tenta recuperar auxiliar. Cria se não existir."""
        try:
            logger.info(f"Tentando recuperar assistente com ID: {params['id']}")
            return client.beta.assistants.retrieve(params["id"])
        except Exception as e:
            logger.warning(f"Não foi possível recuperar o assistente: {str(e)}")
            logger.info(f"Criando novo assistente: {params['name']}")
            tools = [{"type": "function", "function": self._get_function_spec(fn)} 
                     for fn in params["functions"]]
            return client.beta.assistants.create(
                name=params["name"],
                instructions=params["instructions"],
                model=params["model"],
                tools=tools
            )

    def _validate_assistant_tools(self, assistant, required_functions):
        """Confirma se o auxiliar possui as ferramentas necessárias."""
        existing_functions = {tool.function.name for tool in assistant.tools if tool.type == "function"}
        missing = set(required_functions) - existing_functions
        if missing:
            logger.warning(f"Assistente {assistant.name} não possui as funções: {missing}")
            logger.info("Atualizando assistente com as funções necessárias")
            
            # Atualizar o assistente com as ferramentas necessárias
            tools = [{"type": "function", "function": self._get_function_spec(fn)} 
                    for fn in required_functions]
            
            try:
                client.beta.assistants.update(
                    assistant_id=assistant.id,
                    tools=tools
                )
                logger.info(f"Assistente {assistant.name} atualizado com sucesso")
            except Exception as e:
                raise ValueError(
                    f"Erro ao atualizar assistente {assistant.name}: {str(e)}. "
                    "Por favor, atualize no painel da OpenAI ou recrie o assistente."
                )

    def _get_function_spec(self, function_name: str) -> Dict:
        """Define a estrutura das funções disponíveis."""
        functions = {
            "query_whatsapp_messages": {
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
            },
            "log_interaction": {
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
        return functions[function_name]

    def _execute_function(self, function_name: str, arguments: Dict) -> str:
        """Executa a função solicitada, tratando possíveis erros."""
        try:
            if function_name == "query_whatsapp_messages":
                return self._query_whatsapp_data(arguments)
            elif function_name == "log_interaction":
                return self._log_interaction(arguments)
            else:
                return "Função não reconhecida"
        except Exception as e:
            logger.error(f"Erro na execução da função {function_name}: {str(e)}", exc_info=True)
            return f"Erro na execução: {str(e)}"

    def _query_whatsapp_data(self, params: Dict) -> str:
        """Busca registros de WhatsApp aplicando filtros e ordenação."""
        try:
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
            return json.dumps({
                "status": "success",
                "data": result.data,
                "query_params": params
            })
        except Exception as e:
            logger.error(f"Erro na consulta ao Supabase: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e),
                "query_params": params
            })

    def _log_interaction(self, params: Dict) -> str:
        """Grava dados da interação atual."""
        try:
            # Converter timestamp Unix para ISO 8601
            timestamp = params.get("timestamp")
            if isinstance(timestamp, str) and timestamp.replace('.', '').isdigit():
                # Se for um timestamp Unix como string
                timestamp_float = float(timestamp)
                iso_timestamp = datetime.datetime.fromtimestamp(timestamp_float).isoformat()
            else:
                # Usar o timestamp atual se não for válido
                iso_timestamp = datetime.datetime.now().isoformat()
                
            message_data = {
                "thread_id": params["thread_id"],
                "role": params["role"],
                "content": params["content"],
                "timestamp": iso_timestamp,  # Usar o formato ISO
                "user_name": params["user_name"],
                "chatbot_type": params["chatbot_type"]
            }
            supabase.table('mensagens_chatbot').insert(message_data).execute()
            return "Log registrado com sucesso"
        except Exception as e:
            logger.error(f"Erro ao registrar logs: {str(e)}", exc_info=True)
            return f"Erro no registro: {str(e)}"
    
    def _update_user_profile(self, thread_id, user_name):
        """Atualiza o perfil do usuário com base no thread_id."""
        try:
            # Implementação simplificada - pode ser expandida conforme necessário
            logger.info(f"Atualizando perfil do usuário para thread {thread_id} com nome {user_name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do usuário: {str(e)}")
            return False

    def create_thread(self) -> str:
        """Cria uma conversa nova."""
        try:
            thread = client.beta.threads.create()
            logger.info(f"Nova thread criada: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Erro ao criar thread: {str(e)}", exc_info=True)
            raise RuntimeError(f"Não foi possível criar uma nova thread: {str(e)}")

    def process_message(self, chatbot_type: str, user_message: str, thread_id: str = None) -> Dict:
        """Gerencia toda a operação de recepção e processamento da mensagem."""
        try:
            if chatbot_type not in self.assistants:
                logger.error(f"Tipo de chatbot inválido: {chatbot_type}")
                return {"response": f"Erro: tipo de chatbot '{chatbot_type}' não reconhecido", "thread_id": thread_id}
                
            assistant = self.assistants[chatbot_type]
            logger.info(f"Usando assistente: {assistant.id} para chatbot_type: {chatbot_type}")
            
            thread_id = thread_id or self.create_thread()

            # Extrair nome e registrar
            user_name = self.extract_name(user_message) or "Usuário"
            self._log_interaction({
                "thread_id": thread_id,
                "role": "user",
                "content": user_message,
                "timestamp": str(time.time()),
                "user_name": user_name,
                "chatbot_type": chatbot_type
            })
            self._update_user_profile(thread_id, user_name)

            # Adicionar conteúdo na thread
            try:
                client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=user_message
                )
                logger.info(f"Mensagem do usuário adicionada à thread {thread_id}")
            except Exception as e:
                logger.error(f"Erro ao adicionar mensagem à thread: {str(e)}", exc_info=True)
                return {"response": f"Erro ao processar sua mensagem: {str(e)}", "thread_id": thread_id}

            # Dispara execução
            try:
                run = client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant.id
                )
                logger.info(f"Run criado: {run.id}")
            except Exception as e:
                logger.error(f"Erro ao criar run: {str(e)}", exc_info=True)
                return {"response": f"Erro ao iniciar processamento: {str(e)}", "thread_id": thread_id}

            max_attempts = 30  # Limite de tentativas para evitar loops infinitos
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                try:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    
                    logger.info(f"Status do run {run.id}: {run_status.status}")
                    
                    if run_status.status == 'completed':
                        msgs = client.beta.threads.messages.list(thread_id=thread_id)
                        return self._format_response(msgs, thread_id)
                    
                    elif run_status.status == 'failed':
                        error_msg = run_status.last_error.message if hasattr(run_status, 'last_error') else "Erro desconhecido"
                        logger.error(f"Run falhou: {error_msg}")
                        return {"response": f"Desculpe, ocorreu um erro: {error_msg}", "thread_id": thread_id}
                    
                    elif run_status.status == 'requires_action':
                        outputs = []
                        for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                            fn_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)
                            output = self._execute_function(fn_name, args)
                            outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": output
                            })

                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run.id,
                            tool_outputs=outputs
                        )
                        logger.info(f"Outputs de ferramentas enviados para o run {run.id}")
                    
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
            logger.error(f"Tempo limite excedido para o run {run.id}")
            return {"response": "Desculpe, o processamento da sua mensagem demorou muito tempo. Por favor, tente novamente.", "thread_id": thread_id}

        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {str(e)}", exc_info=True)
            return {"response": f"Erro no processamento: {str(e)}", "thread_id": thread_id}

    def _format_response(self, messages, thread_id: str) -> Dict:
        """Prepara a saída final."""
        try:
            if not messages.data:
                logger.warning(f"Nenhuma mensagem encontrada para thread_id: {thread_id}")
                return {
                    "response": "Desculpe, não foi possível gerar uma resposta.",
                    "thread_id": thread_id,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
            last_message = messages.data[0].content[0].text.value
            # Usar formato ISO 8601 para o timestamp
            iso_timestamp = datetime.datetime.now().isoformat()
            
            return {
                "response": last_message,
                "thread_id": thread_id,
                "timestamp": iso_timestamp,
                "metadata": {
                    "sources": self._extract_sources(last_message),
                    "entities": self._extract_entities(last_message)
                }
            }
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar a resposta.",
                "thread_id": thread_id,
                "timestamp": datetime.datetime.now().isoformat()
            }

    def extract_name(self, message: str) -> Optional[str]:
        """Recupera o primeiro nome detectado ou 'Nenhum nome encontrado'."""
        try:
            temp_thread = self.create_thread()
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content="Você é um especialista em extrair nomes. Retorne apenas o primeiro nome encontrado ou 'Nenhum nome encontrado'."
            )
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content=f"Extraia o nome desta mensagem: '{message}'"
            )
            run = client.beta.threads.runs.create(
                thread_id=temp_thread,
                assistant_id=self.assistants["whatsapp"].id
            )
            self._wait_for_run_completion(temp_thread, run.id)

            msgs = client.beta.threads.messages.list(thread_id=temp_thread)
            if msgs.data:
                extracted = msgs.data[0].content[0].text.value.strip()
                return None if "nenhum" in extracted.lower() else extracted
            return None
        except Exception as e:
            logger.error(f"Erro na extração de nome: {e}", exc_info=True)
            return None

    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """Produz um resumo em HTML para as mensagens."""
        try:
            system_msg = (
                "Você é um analista de textos. Formate o resumo em HTML usando: "
                "<h3> para títulos, <ul>/<li> para listas e <strong> para destaques."
            )
            user_msg = "Resuma:\n\n" + "\n".join(
                f"{m['sender_name']}: {m['content']}" for m in messages
            )
            response = client.chat.completions.create(
                model="gpt-4o",  # Atualizado para um modelo mais estável
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}", exc_info=True)
            return f"Erro ao gerar resumo: {str(e)}"

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 30):
        """Aguarda o encerramento de uma execução dentro do prazo."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                if status.status == "completed":
                    return
                elif status.status == "failed":
                    error_msg = status.last_error.message if hasattr(status, 'last_error') else "Erro desconhecido"
                    raise RuntimeError(f"Falha na execução: {error_msg}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro ao verificar status do run: {str(e)}", exc_info=True)
                raise
        raise TimeoutError("Tempo esgotado para resposta do assistente")

    def _extract_sources(self, text: str) -> List[str]:
        """Simula extração de trechos como possíveis fontes."""
        return [text[i:i+50] for i in range(0, len(text), 50)][:3]

    def _extract_entities(self, text: str) -> Dict:
        """Identifica possíveis entidades no conteúdo."""
        return {"pessoas": [], "organizações": [], "locais": []}

    def _verify_supabase_access(self):
        """Checa permissões de leitura/escrita e colunas relevantes."""
        required_access = {
            'whatsapp_messages': ['SELECT'],
            'mensagens_chatbot': ['INSERT', 'UPDATE'],
            'usuarios_chatbot': ['SELECT', 'UPDATE']
        }
        for table, permissions in required_access.items():
            try:
                supabase.table(table).select('*').limit(1).execute()
                logger.info(f"Acesso verificado para tabela: {table}")
            except Exception as e:
                logger.error(f"Acesso negado à tabela {table}: {str(e)}", exc_info=True)
                raise PermissionError(f"Acesso negado à tabela {table}: {str(e)}")

        # Verificação opcional de colunas específicas (exemplo)
        required_columns = {
            'mensagens_chatbot': ['user_name'],
            'usuarios_chatbot': ['user_name']
        }
        # Checagens simbólicas: em um cenário real, seria preciso mapear colunas disponíveis
        for t, cols in required_columns.items():
            # Caso desejássemos verificar colunas, poderíamos fazer algo mais complexo
            logger.info(f"Verificando colunas esperadas em {t}: {cols}")