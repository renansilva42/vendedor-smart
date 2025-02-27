from supabase import create_client, Client
from config import Config
import datetime
import pytz
import uuid
from typing import Optional, Dict, List
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do fuso horário
TIMEZONE = pytz.timezone('America/Belem')

# Inicialização do cliente Supabase
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class Auth:
    @staticmethod
    def verify_credentials(email: str, password: str) -> bool:
        """
        Verifica se as credenciais do usuário são válidas.
        """
        try:
            response = supabase.table('usuarios_autorizados').select('*').eq('email', email).execute()
            if response.data:
                user = response.data[0]
                if user['password'] == password:  # Comparação direta
                    return True
            return False
        except Exception as e:
            print(f"Erro ao verificar credenciais: {e}")
            return False

class User:
    @staticmethod
    def create(user_id, name=None, email=None):
        print(f"Criando usuário: {user_id}, nome: {name}, email: {email}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            user_data = {
                'id': user_id,
                'name': name or "Usuário Anônimo",
                'email': email,
                'last_interaction': current_time
            }
            response = supabase.table('usuarios_chatbot').insert(user_data).execute()
            print(f"Usuário criado com sucesso: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            return None

    @staticmethod
    def update_thread_id(user_id, thread_id, chatbot_type):
        print(f"Atualizando thread_id para usuário {user_id}: {thread_id}, tipo: {chatbot_type}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            update_data = {
                'last_interaction': current_time,
                f'thread_id_{chatbot_type}': thread_id
            }
            response = supabase.table('usuarios_chatbot').update(update_data).eq('id', user_id).execute()
            print(f"Thread_id atualizado com sucesso: {response.data}")
        except Exception as e:
            print(f"Erro ao atualizar thread_id: {e}")
            raise

    @staticmethod
    def update_last_interaction(user_id, chatbot_type):
        print(f"Atualizando última interação para usuário: {user_id}, tipo: {chatbot_type}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            response = supabase.table('usuarios_chatbot').update({
                'last_interaction': current_time
            }).eq('id', user_id).execute()
            print(f"Última interação atualizada com sucesso: {response.data}")
        except Exception as e:
            print(f"Erro ao atualizar última interação: {e}")
            raise
        
    @staticmethod
    def get_or_create_by_email(email: str) -> Optional[Dict]:
        """
        Obtém um usuário pelo email ou cria um novo se não existir.
        Incrementa o contador de login.
        """
        if not email:
            logger.warning("Tentativa de obter usuário com email vazio")
            return None
            
        try:
            response = supabase.table('usuarios_chatbot').select('*').eq('email', email).execute()
            if response.data:
                user = response.data[0]
                # Incrementa o contador de login
                updated_user = User.increment_login_count(user['id'])
                return updated_user if updated_user else user
            else:
                user_id = str(uuid.uuid4())
                return User.create(user_id, name="Usuário Anônimo", email=email, login_count=1)
        except Exception as e:
            logger.error(f"Erro ao obter ou criar usuário por email: {e}")
            return {"error": str(e)}


    @staticmethod
    def increment_login_count(user_id: str) -> Optional[Dict]:
        """
        Incrementa o contador de login do usuário.
        """
        try:
            # Primeiro, obtemos o valor atual do login_count
            get_response = supabase.table('usuarios_chatbot').select('login_count').eq('id', user_id).execute()
            if get_response.data:
                current_count = get_response.data[0]['login_count'] or 0
            else:
                current_count = 0

            # Agora, incrementamos o valor
            new_count = current_count + 1
            update_response = supabase.table('usuarios_chatbot').update({
                'login_count': new_count,
                'last_interaction': datetime.datetime.now(TIMEZONE).isoformat()
            }).eq('id', user_id).execute()
        
            print(f"Contador de login incrementado: {update_response.data}")
            return update_response.data[0] if update_response.data else None
        except Exception as e:
            print(f"Erro ao incrementar contador de login: {e}")
            return None

    @staticmethod
    def create(user_id, name=None, email=None, login_count=1):
        print(f"Criando usuário: {user_id}, nome: {name}, email: {email}, login_count: {login_count}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            user_data = {
                'id': user_id,
                'name': name or "Usuário Anônimo",
                'email': email,
                'last_interaction': current_time,
                'login_count': login_count
            }
            response = supabase.table('usuarios_chatbot').insert(user_data).execute()
            print(f"Usuário criado com sucesso: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            return None

    @staticmethod
    def get_thread_id(user_id: str, chatbot_type: str) -> Optional[str]:
        try:
            response = supabase.table('usuarios_chatbot').select(f'thread_id_{chatbot_type}').eq('id', user_id).execute()
            if response.data:
                return response.data[0][f'thread_id_{chatbot_type}']
            return None
        except Exception as e:
            print(f"Erro ao obter thread_id: {e}")
            return None

    @staticmethod
    def get_name(user_id: str) -> str:
        try:
            response = supabase.table('usuarios_chatbot').select('name').eq('id', user_id).execute()
            if response.data and response.data[0]['name'] not in ["Usuário Anônimo", "Nenhum nome encontrado"]:
                return response.data[0]['name']
            return "Usuário Anônimo"
        except Exception as e:
            print(f"Erro ao obter nome do usuário: {e}")
            return "Usuário Anônimo"

    @staticmethod
    def update_name(user_id: str, name: str) -> Optional[Dict]:
        try:
            print(f"Tentando atualizar nome do usuário {user_id} para '{name}' no Supabase")
            response = supabase.table('usuarios_chatbot').update({'name': name}).eq('id', user_id).execute()
            print(f"Resposta do Supabase ao atualizar nome: {response}")
            if response.data:
                print(f"Nome do usuário atualizado com sucesso no Supabase: {name}")
                return response.data[0]
            else:
                print(f"Nenhum usuário encontrado com o ID: {user_id}")
                return None
        except Exception as e:
            print(f"Erro ao atualizar nome do usuário no Supabase: {e}")
            return None
        
    @staticmethod
    def get_login_count(user_id):
        try:
            response = supabase.table('usuarios_chatbot').select('login_count').eq('id', user_id).execute()
            if response.data:
                return response.data[0]['login_count']
            return 0
        except Exception as e:
            print(f"Erro ao obter contagem de logins: {e}")
            return 0

class Message:
    @staticmethod
    def create(thread_id, role, content, user_id=None, chatbot_type=None, user_name=None):
        print(f"Criando mensagem: thread_id={thread_id}, role={role}, user_id={user_id}, chatbot_type={chatbot_type}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            message_data = {
                'thread_id': thread_id,
                'role': role,
                'content': content,
                'timestamp': current_time,
                'chatbot_type': chatbot_type,
                'user_name': user_name if user_name and user_name != "Usuário Anônimo" else ('Assistente IA' if role == 'assistant' else 'Usuário')
            }
        
            response = supabase.table('mensagens_chatbot').insert(message_data).execute()
            print(f"Mensagem criada com sucesso: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao criar mensagem: {e}")
            raise

    @staticmethod
    def get_messages(thread_id: str, chatbot_type: str) -> List[Dict]:
        try:
            response = supabase.table('mensagens_chatbot').select('*').eq('thread_id', thread_id).eq('chatbot_type', chatbot_type).order('timestamp', desc=False).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao obter mensagens: {e}")
            return []
    @staticmethod
    def update_user_name(thread_id: str, user_id: str, new_name: str):
        try:
            response = supabase.table('mensagens_chatbot').update({
                'user_name': new_name
            }).eq('thread_id', thread_id).eq('role', 'user').execute()
            print(f"Nomes de usuário atualizados nas mensagens: {response.data}")
        except Exception as e:
            print(f"Erro ao atualizar nomes de usuário nas mensagens: {e}")
            
    @staticmethod
    def calculate_conversation_scores(user_id):
        # Implemente a lógica para calcular os scores das conversas
        # Isso pode envolver análise de sentimento, contagem de palavras-chave, etc.
        # Por enquanto, retornaremos valores de exemplo
        return {
            'lead_score': 75,
            'ia_conversation_score': 85,
            'ia_evaluation_score': 90
        }

    @staticmethod
    def get_ia_feedback(user_id):
        # Implemente a lógica para gerar feedback da IA
        # Isso pode envolver análise das últimas conversas e uso de prompts específicos para a IA
        return "O vendedor poderia ter sido mais assertivo na apresentação dos benefícios do produto."

    @staticmethod
    def analyze_positioning(user_id):
        # Implemente a lógica para analisar o posicionamento do vendedor
        # Isso pode envolver comparação das mensagens do vendedor com os valores da empresa
        return "O vendedor demonstra bom alinhamento com os valores da empresa, mas pode melhorar na comunicação da proposta de valor."
    
    @staticmethod
    def get_whatsapp_messages():
        try:
            response = supabase.table('whatsapp_messages').select('*').order('timestamp', desc=True).limit(100).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar mensagens do WhatsApp: {e}")
            return []

# Remova ou comente as funções de exemplo no final do arquivo, se não forem mais necessárias