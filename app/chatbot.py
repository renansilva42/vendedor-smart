# app/chatbot.py
from openai import OpenAI
from config import Config
import time
import json
from typing import Optional, List, Dict
from supabase import create_client
import logging

client = OpenAI(api_key=Config.OPENAI_API_KEY)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Configuração de logging para depuração
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class Chatbot:  # Mantendo o nome original para compatibilidade
    def __init__(self, chatbot_type: str):
        self.manager = ChatbotManager()
        self.chatbot_type = chatbot_type

    def create_thread(self) -> str:
        return self.manager.create_thread()

    def send_message(self, thread_id: str, message: str) -> str:
        response = self.manager.process_message(
            chatbot_type=self.chatbot_type,
            user_message=message,
            thread_id=thread_id
        )
        return response.get('response', 'Desculpe, não foi possível gerar uma resposta.')

    # Mantemos todos os métodos originais como wrappers
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
        self._verify_supabase_access()

    def _initialize_assistants(self):
        """Cria ou recupera assistentes com verificação de ferramentas"""
        assistants_map = {
            "atual": {
                "name": "Assistente de Vendas",
                "functions": ["query_whatsapp_messages", "log_interaction"],
                "model": "gpt-4o-mini-2024-07-18",
                "instructions": (
                    "Você é um especialista em vendas. Use query_whatsapp_messages para acessar "
                    "histórico de conversas do WhatsApp. Sempre que o usuário mencionar 'histórico', "
                    "'mensagens anteriores' ou pedir para 'consultar conversas', utilize a função."
                ),
                "id": Config.ASSISTANT_ID_VENDAS
            },
            "novo": {
                "name": "Assistente de Treinamento",
                "functions": ["log_interaction"],
                "model": "gpt-4o-mini-2024-07-18",
                "instructions": "Você é um tutor especializado em treinamento corporativo.",
                "id": Config.ASSISTANT_ID_TREINAMENTO
            },
            "whatsapp": {
                "name": "Assistente WhatsApp",
                "functions": [],
                "model": "gpt-4o-mini-2024-07-18",
                "instructions": "Você é especialista em análise de conversas do WhatsApp.",
                "id": Config.ASSISTANT_ID_WHATSAPP
            }
        }

        for key, params in assistants_map.items():
            assistant = self._get_or_create_assistant(params)
            self._validate_assistant_tools(assistant, params["functions"])
            self.assistants[key] = assistant

    def _get_or_create_assistant(self, params: Dict):
        """Pilar 1: Gestão inteligente de assistentes"""
        try:
            return client.beta.assistants.retrieve(params["id"])
        except Exception as e:
            tools = [{"type": "function", "function": self._get_function_spec(fn)} 
                     for fn in params["functions"]]
            
            return client.beta.assistants.create(
                name=params["name"],
                instructions=params["instructions"],
                model=params["model"],
                tools=tools
            )

    def _validate_assistant_tools(self, assistant, required_functions):
        """Verifica e atualiza ferramentas do assistente se necessário"""
        existing_functions = {tool.function.name for tool in assistant.tools if tool.type == "function"}
        
        missing = set(required_functions) - existing_functions
        if missing:
            raise ValueError(f"Assistente {assistant.name} está faltando funções: {missing}. "
                             "Atualize manualmente no painel da OpenAI ou recrie o assistente.")
        
    def _get_function_spec(self, function_name: str) -> Dict:
        """Pilar 2: Definição estruturada de funções"""
        functions = {
            "query_whatsapp_messages": {
                "name": "query_whatsapp_messages",
                "description": "Consulta mensagens históricas do WhatsApp com filtros avançados",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sender_name": {
                            "type": "string",
                            "description": "Nome parcial ou completo do remetente"
                        },
                        "content": {
                            "type": "string",
                            "description": "Termo de busca no conteúdo da mensagem"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Data inicial no formato YYYY-MM-DD"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Data final no formato YYYY-MM-DD"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Número máximo de resultados (padrão: 10)",
                            "default": 10
                        }
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
                        "user_message": {"type": "string"},
                        "assistant_response": {"type": "string"},
                        "metadata": {"type": "object"}
                    },
                    "required": ["thread_id", "user_message"]
                }
            }
        }
        return functions[function_name]

    def _execute_function(self, function_name: str, arguments: Dict) -> str:
        """Pilar 6: Execução de funções com tratamento de erros"""
        try:
            if function_name == "query_whatsapp_messages":
                return self._query_whatsapp_data(arguments)
            elif function_name == "log_interaction":
                return self._log_interaction(arguments)
            else:
                return "Função não implementada"
        except Exception as e:
            return f"Erro na execução: {str(e)}"

    def _query_whatsapp_data(self, params: Dict) -> str:
        """Consulta avançada com tratamento de datas e paginação"""
        try:
            query = supabase.table('whatsapp_messages').select('*')
            
            # Filtros básicos
            if params.get('sender_name'):
                query = query.ilike('sender_name', f"%{params['sender_name']}%")
            if params.get('content'):
                query = query.ilike('content', f"%{params['content']}%")
            
            # Filtro temporal (novo)
            if params.get('start_date') and params.get('end_date'):
                query = query.gte('timestamp', params['start_date']).lte('timestamp', params['end_date'])
            
            # Ordenação e paginação
            query = query.order('timestamp', desc=True).limit(params.get('limit', 10))
            
            result = query.execute()
            
            # Log para depuração
            logger.info(f"Consulta Supabase: {len(result.data)} resultados")
            return json.dumps({
                "status": "success",
                "data": result.data,
                "query_params": params
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "query_params": params
            })

    def _log_interaction(self, params: Dict) -> str:
        """Registro duplo de interações"""
        try:
            # Registro na tabela de mensagens
            message_data = {
                "thread_id": params["thread_id"],
                "role": "assistant" if params.get("assistant_response") else "user",
                "content": params.get("assistant_response") or params["user_message"],
                "chatbot_type": "atual" if "atual" in params["thread_id"] else "novo",
                "timestamp": str(time.time())
            }
            supabase.table('mensagens_chatbot').insert(message_data).execute()
            
            # Atualização do usuário
            user_data = {
                "id": params["thread_id"],
                "last_interaction": str(time.time()),
                "login_count": 1
            }
            supabase.table('usuarios_chatbot').upsert(user_data).execute()
            
            return "Log registrado com sucesso"
        except Exception as e:
            return f"Erro no registro: {str(e)}"

    def create_thread(self) -> str:
        """Cria uma nova thread de conversa"""
        thread = client.beta.threads.create()
        return thread.id

    def process_message(self, chatbot_type: str, user_message: str, thread_id: str = None) -> Dict:
        """Pilar 5: Processamento completo de mensagens"""
        try:
            assistant = self.assistants[chatbot_type]
            thread_id = thread_id or self.create_thread()
            
            # Registro inicial da mensagem
            self._log_interaction({
                "thread_id": thread_id,
                "user_message": user_message
            })
            
            # Adiciona mensagem à thread
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            
            # Inicia execução
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant.id
            )
            
            # Monitoramento da execução
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    return self._format_response(messages, thread_id)
                    
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
                
                time.sleep(1)
                
        except Exception as e:
            return {"error": str(e)}

    def _format_response(self, messages, thread_id: str) -> Dict:
        """Pilar 7: Formatação final da resposta"""
        last_message = messages.data[0].content[0].text.value
        return {
            "response": last_message,
            "thread_id": thread_id,
            "timestamp": str(time.time()),
            "metadata": {
                "sources": self._extract_sources(last_message),
                "entities": self._extract_entities(last_message)
            }
        }

    def extract_name(self, message: str) -> Optional[str]:
        """Extrai nomes usando técnica específica"""
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
            
            messages = client.beta.threads.messages.list(thread_id=temp_thread)
            if messages.data:
                extracted = messages.data[0].content[0].text.value.strip()
                return None if "nenhum" in extracted.lower() else extracted
            return None
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            return None

    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """Gera resumo formatado de conversas"""
        try:
            system_msg = """Você é um analista de conversas. Formate o resumo em HTML com:
            - <h3> para títulos
            - <ul>/<li> para listas
            - <strong> para ênfase"""
            
            user_msg = "Resuma estas mensagens:\n\n" + "\n".join(
                f"{m['sender_name']}: {m['content']}" for m in messages
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro na geração: {str(e)}"

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 30):
        """Aguarda conclusão da execução"""
        start = time.time()
        while time.time() - start < timeout:
            status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            
            if status.status == "completed":
                return
            elif status.status == "failed":
                raise RuntimeError(f"Falha na execução: {status.last_error}")
            
            time.sleep(1)
        raise TimeoutError("Tempo excedido para resposta do assistente")

    def _extract_sources(self, text: str) -> List[str]:
        """Extrai fontes mencionadas no texto"""
        return [text[i:i+50] for i in range(0, len(text), 50)][:3]

    def _extract_entities(self, text: str) -> Dict:
        """Identifica entidades principais"""
        return {"pessoas": [], "organizações": [], "locais": []}

    def _verify_supabase_access(self):
        """Verifica permissões essenciais"""
        required_access = {
            'whatsapp_messages': ['SELECT'],
            'mensagens_chatbot': ['INSERT', 'UPDATE'],
            'usuarios_chatbot': ['SELECT', 'UPDATE']
        }
        
        for table, permissions in required_access.items():
            try:
                supabase.table(table).select('*').limit(1).execute()
            except Exception as e:
                raise PermissionError(f"Acesso negado à tabela {table}: {str(e)}")

# Teste manual no código
def test_whatsapp_query():
    manager = ChatbotManager()
    params = {
        "sender_name": "João",
        "content": "pagamento",
        "limit": 2
    }
    result = manager._query_whatsapp_data(params)
    print("Resultado do teste:", json.loads(result))
