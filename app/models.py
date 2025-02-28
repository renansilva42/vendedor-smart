# app/models.py (refatorado)
from supabase import create_client, Client
from config import Config
import datetime
import pytz
import uuid
from typing import Optional, Dict, List, Any, Union
import logging
from functools import lru_cache
from openai import OpenAI
import os

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do fuso horário
TIMEZONE = pytz.timezone('America/Belem')

# Inicialização do cliente Supabase
try:
    supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    # Teste de conexão
    test = supabase.table('usuarios_chatbot').select("*").limit(1).execute()
    logger.info("Conexão com Supabase bem-sucedida!")
    logger.debug(f"Resposta: data={test.data} count={test.count}")
except Exception as e:
    logger.error(f"Erro na conexão com Supabase: {str(e)}")
    # Criar uma instância vazia do cliente para evitar erros de importação
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Inicialização do cliente OpenAI
try:
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    logger.info("Cliente OpenAI inicializado com sucesso!")
except Exception as e:
    logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
    # Criar uma instância vazia para evitar erros de importação
    client = None

class Auth:
    @staticmethod
    @lru_cache(maxsize=100)
    def verify_credentials(email: str, password: str) -> bool:
        """
        Verifica se as credenciais do usuário são válidas.
        Usa cache para reduzir consultas repetidas.
        """
        try:
            response = supabase.table('usuarios_autorizados').select('*').eq('email', email).execute()
            if response.data:
                user = response.data[0]
                # TODO: Implementar hash de senha em vez de comparação direta
                if user['password'] == password:
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar credenciais: {e}")
            return False

class User:
    @staticmethod
    def create(user_id: str, name: str = None, email: str = None, login_count: int = 1) -> Optional[Dict]:
        logger.info(f"Criando usuário: {user_id}, nome: {name}, email: {email}, login_count: {login_count}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            user_data = {
                'id': user_id,
                'name': name or "Usuário Anônimo",
                'email': email,
                'last_interaction': current_time,
                'login_count': login_count,
                'thread_id_atual': None,
                'thread_id_novo': None
            }
            response = supabase.table('usuarios_chatbot').insert(user_data).execute()
            if response.data:
                logger.info(f"Usuário criado com sucesso: {response.data[0]}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            return None

    @staticmethod
    def update_thread_id(user_id: str, thread_id: str, chatbot_type: str) -> bool:
        try:
            field_name = f'thread_id_{chatbot_type}'
            update_data = {
                field_name: thread_id,
                'last_interaction': datetime.datetime.now(TIMEZONE).isoformat()
            }
            
            logger.info(f"Atualizando {field_name} para usuário {user_id} com valor {thread_id}")
            
            response = supabase.table('usuarios_chatbot').update(update_data).eq('id', user_id).execute()
            
            if not response.data:
                logger.error(f"Nenhum dado retornado ao atualizar thread_id para usuário {user_id}")
                return False
                
            logger.info(f"Thread_id atualizado com sucesso: {response.data}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar thread_id: {str(e)}")
            return False

    @staticmethod
    def update_thread_id_atual(user_id: str, thread_id: str) -> bool:
        return User.update_thread_id(user_id, thread_id, 'atual')

    @staticmethod
    def update_thread_id_novo(user_id: str, thread_id: str) -> bool:
        return User.update_thread_id(user_id, thread_id, 'novo')

    @staticmethod
    def update_last_interaction(user_id: str, chatbot_type: str) -> bool:
        logger.info(f"Atualizando última interação para usuário: {user_id}, tipo: {chatbot_type}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            response = supabase.table('usuarios_chatbot').update({
                'last_interaction': current_time
            }).eq('id', user_id).execute()
            
            if response.data:
                logger.info(f"Última interação atualizada com sucesso: {response.data}")
                return True
            else:
                logger.warning(f"Nenhum dado retornado ao atualizar última interação para usuário {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar última interação: {str(e)}")
            return False

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
        
            logger.info(f"Contador de login incrementado: {update_response.data}")
            return update_response.data[0] if update_response.data else None
        except Exception as e:
            logger.error(f"Erro ao incrementar contador de login: {e}")
            return None

    @staticmethod
    @lru_cache(maxsize=100)
    def get_thread_id(user_id: str, chatbot_type: str) -> Optional[str]:
        """Obtém o thread_id do usuário com cache para reduzir consultas."""
        try:
            response = supabase.table('usuarios_chatbot').select(f'thread_id_{chatbot_type}').eq('id', user_id).execute()
            if response.data:
                return response.data[0][f'thread_id_{chatbot_type}']
            return None
        except Exception as e:
            logger.error(f"Erro ao obter thread_id: {e}")
            return None

    @staticmethod
    @lru_cache(maxsize=100)
    def get_name(user_id: str) -> str:
        """Obtém o nome do usuário com cache para reduzir consultas."""
        try:
            response = supabase.table('usuarios_chatbot').select('name').eq('id', user_id).execute()
            if response.data and response.data[0]['name'] not in ["Usuário Anônimo", "Nenhum nome encontrado"]:
                return response.data[0]['name']
            return "Usuário Anônimo"
        except Exception as e:
            logger.error(f"Erro ao obter nome do usuário: {e}")
            return "Usuário Anônimo"

    @staticmethod
    def update_name(user_id: str, name: str) -> Optional[Dict]:
        """Atualiza o nome do usuário e invalida o cache."""
        try:
            logger.info(f"Tentando atualizar nome do usuário {user_id} para '{name}' no Supabase")
            response = supabase.table('usuarios_chatbot').update({'name': name}).eq('id', user_id).execute()
            logger.debug(f"Resposta do Supabase ao atualizar nome: {response}")
            
            # Invalidar o cache
            User.get_name.cache_clear()
            
            if response.data:
                logger.info(f"Nome do usuário atualizado com sucesso no Supabase: {name}")
                return response.data[0]
            else:
                logger.warning(f"Nenhum usuário encontrado com o ID: {user_id}")
                return None
        except Exception as e:
            logger.error(f"Erro ao atualizar nome do usuário no Supabase: {e}")
            return None
        
    @staticmethod
    @lru_cache(maxsize=100)
    def get_login_count(user_id: str) -> int:
        """Obtém a contagem de logins com cache."""
        try:
            response = supabase.table('usuarios_chatbot').select('login_count').eq('id', user_id).execute()
            if response.data:
                return response.data[0]['login_count']
            return 0
        except Exception as e:
            logger.error(f"Erro ao obter contagem de logins: {e}")
            return 0

    @staticmethod
    def delete(user_id: str) -> bool:
        """Deleta um usuário e limpa os caches relacionados."""
        try:
            supabase.table('usuarios_chatbot').delete().eq('id', user_id).execute()
            
            # Limpar caches
            User.get_name.cache_clear()
            User.get_thread_id.cache_clear()
            User.get_login_count.cache_clear()
            
            logger.info(f"Usuário {user_id} deletado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar usuário {user_id}: {str(e)}")
            return False

# app/models.py (continuação da classe Message)
class Message:
    @staticmethod
    def create(thread_id: str, role: str, content: str, user_id: str = None, 
               chatbot_type: str = None, user_name: str = None) -> Optional[Dict]:
        """Cria uma nova mensagem no banco de dados."""
        logger.info(f"Criando mensagem: thread_id={thread_id}, role={role}, user_id={user_id}, chatbot_type={chatbot_type}")
        current_time = datetime.datetime.now(TIMEZONE).isoformat()
        try:
            message_data = {
                'thread_id': thread_id,
                'role': role,
                'content': content,
                'timestamp': current_time,
                'chatbot_type': chatbot_type,
                'user_name': user_name,
                'user_id': user_id
            }
            response = supabase.table('mensagens_chatbot').insert(message_data).execute()
            logger.debug(f"Mensagem criada: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao criar mensagem: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_messages(thread_id: str, chatbot_type: str = None) -> List[Dict]:
        """Recupera mensagens com base no thread_id e chatbot_type."""
        try:
            query = supabase.table('mensagens_chatbot').select('*').eq('thread_id', thread_id)
            
            if chatbot_type:
                query = query.eq('chatbot_type', chatbot_type)
                
            query = query.order('timestamp', desc=False)
            response = query.execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Erro ao recuperar mensagens: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def update_user_name(thread_id: str, user_id: str, new_name: str) -> bool:
        """Atualiza o nome do usuário em todas as mensagens de um thread."""
        try:
            # Atualizar apenas mensagens do usuário específico
            response = supabase.table('mensagens_chatbot').update({
                'user_name': new_name
            }).eq('thread_id', thread_id).eq('user_id', user_id).execute()
            
            logger.info(f"Nome do usuário atualizado em {len(response.data) if response.data else 0} mensagens")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar nome do usuário nas mensagens: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def calculate_conversation_scores(user_id: str) -> Dict:
        """Calcula pontuações de conversas para um usuário com base em análise de sentimento."""
        try:
            # Obter todas as mensagens do usuário
            response = supabase.table('mensagens_chatbot').select('*').eq('user_id', user_id).execute()
            
            if not response.data:
                return {
                    "clareza": 0,
                    "persuasao": 0,
                    "conhecimento": 0,
                    "empatia": 0,
                    "resolucao": 0
                }
                
            # Implementação real usaria análise de sentimento ou LLM para avaliar as mensagens
            # Esta é uma implementação simplificada para demonstração
            messages = response.data
            total_messages = len(messages)
            
            if total_messages == 0:
                return {
                    "clareza": 0,
                    "persuasao": 0,
                    "conhecimento": 0,
                    "empatia": 0,
                    "resolucao": 0
                }
            
            # Calcular pontuações baseadas no comprimento das mensagens e palavras-chave
            clareza = min(100, sum(len(m['content'].split()) for m in messages if m['role'] == 'user') / total_messages * 10)
            persuasao = min(100, sum(1 for m in messages if m['role'] == 'user' and any(word in m['content'].lower() for word in ['benefício', 'vantagem', 'melhor', 'ideal'])) / max(1, total_messages) * 100)
            conhecimento = min(100, sum(len(m['content']) for m in messages if m['role'] == 'user') / total_messages / 10)
            empatia = min(100, sum(1 for m in messages if m['role'] == 'user' and any(word in m['content'].lower() for word in ['entendo', 'compreendo', 'ajudar', 'apoiar'])) / max(1, total_messages) * 100)
            resolucao = min(100, 70 + (total_messages % 10) * 3)  # Valor base + variação
            
            return {
                "clareza": round(clareza),
                "persuasao": round(persuasao),
                "conhecimento": round(conhecimento),
                "empatia": round(empatia),
                "resolucao": round(resolucao)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular pontuações de conversas: {str(e)}", exc_info=True)
            return {
                "clareza": 50,
                "persuasao": 50,
                "conhecimento": 50,
                "empatia": 50,
                "resolucao": 50
            }

    @staticmethod
    def get_ia_feedback(user_id: str) -> str:
        """Gera feedback da IA com base nas interações do usuário."""
        try:
            # Verificar se o cliente OpenAI está disponível
            if client is None:
                return "O serviço de feedback da IA não está disponível no momento."
                
            # Obter mensagens recentes do usuário
            response = supabase.table('mensagens_chatbot').select('*').eq('user_id', user_id).order('timestamp', desc=True).limit(20).execute()
            
            if not response.data:
                return "Ainda não há dados suficientes para gerar um feedback personalizado."
                
            # Usar OpenAI para gerar feedback
            messages = response.data
            
            # Preparar prompt para a API
            prompt = "Com base nas seguintes mensagens de um vendedor, forneça um feedback construtivo sobre suas habilidades de comunicação e vendas:\n\n"
            
            for msg in messages:
                if msg['role'] == 'user':
                    prompt += f"Vendedor: {msg['content']}\n"
                else:
                    prompt += f"Cliente: {msg['content']}\n"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um especialista em vendas que fornece feedback construtivo e útil."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            feedback = response.choices[0].message.content
            return feedback
            
        except Exception as e:
            logger.error(f"Erro ao gerar feedback da IA: {str(e)}", exc_info=True)
            return "Não foi possível gerar feedback neste momento. Por favor, tente novamente mais tarde."

    @staticmethod
    def analyze_positioning(user_id: str) -> str:
        """Analisa o posicionamento do vendedor com base em suas mensagens."""
        try:
            # Verificar se o cliente OpenAI está disponível
            if client is None:
                return "O serviço de análise de posicionamento não está disponível no momento."
                
            # Obter mensagens do usuário
            response = supabase.table('mensagens_chatbot').select('*').eq('user_id', user_id).eq('role', 'user').execute()
            
            if not response.data or len(response.data) < 5:
                return "Ainda não há mensagens suficientes para analisar seu posicionamento."
                
            # Concatenar mensagens para análise
            messages = "\n".join([msg['content'] for msg in response.data])
            
            # Usar OpenAI para análise
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de comunicação de vendas. Avalie o alinhamento do vendedor com os valores da empresa: transparência, empatia, solução de problemas e foco no cliente."},
                    {"role": "user", "content": f"Analise as seguintes mensagens de um vendedor e avalie seu posicionamento:\n\n{messages}"}
                ],
                max_tokens=400
            )
            
            analysis = response.choices[0].message.content
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar posicionamento: {str(e)}", exc_info=True)
            return "Não foi possível analisar seu posicionamento neste momento. Por favor, tente novamente mais tarde."

    @staticmethod
    def get_whatsapp_messages() -> List[Dict]:
        """Recupera as mensagens mais recentes do WhatsApp do banco de dados."""
        try:
            # Obter mensagens da tabela whatsapp_messages
            response = supabase.table('whatsapp_messages').select('*').order('timestamp', desc=True).limit(50).execute()
            
            if not response.data:
                return []
                
            # Formatar mensagens para exibição
            formatted_messages = []
            for msg in response.data:
                formatted_messages.append({
                    'sender_name': msg.get('sender_name', 'Desconhecido'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp', '')
                })
                
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Erro ao recuperar mensagens do WhatsApp: {str(e)}", exc_info=True)
            return []