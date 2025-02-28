# app/chatbot.py
from openai import OpenAI
from config import Config
import time
import json
from typing import Optional, List, Dict
from supabase import create_client
import logging
import datetime
import re

client = OpenAI(api_key=Config.OPENAI_API_KEY)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class ChatbotFactory:
    @staticmethod
    def create_chatbot(chatbot_type: str) -> 'Chatbot':
        return Chatbot(chatbot_type)

class Chatbot:
    def __init__(self, chatbot_type: str):
        self.chatbot_type = chatbot_type
        self.assistant_id = self._get_assistant_id()
        logger.info(f"Assistente recuperado: {self._get_assistant_name()} (ID: {self.assistant_id})")

    def _get_assistant_id(self) -> str:
        if self.chatbot_type == 'atual':
            return Config.ASSISTANT_ID_VENDAS
        elif self.chatbot_type == 'novo':
            return Config.ASSISTANT_ID_TREINAMENTO
        elif self.chatbot_type == 'whatsapp':
            return Config.ASSISTANT_ID_WHATSAPP
        else:
            raise ValueError(f"Tipo de chatbot inválido: {self.chatbot_type}")

    def _get_assistant_name(self) -> str:
        assistant = client.beta.assistants.retrieve(self.assistant_id)
        return assistant.name

    def create_thread(self) -> str:
        thread = client.beta.threads.create()
        return thread.id

    def send_message(self, thread_id: str, message: str, user_name: str = "Usuário") -> Dict:
        try:
            # Verificar se é uma mensagem de apresentação e extrair nome
            extracted_name = self.extract_name(message)
            if extracted_name:
                user_name = extracted_name
                # Atualizar o nome no Supabase
                from app.models import User
                user_id = None
                # Tentar obter user_id da sessão Flask
                from flask import session
                if session and 'user_id' in session:
                    user_id = session.get('user_id')
                if user_id:
                    User.update_name(user_id, user_name)

            # Adicionar mensagem à thread
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            # Criar e executar o run com temperatura mais baixa para respostas mais rápidas
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                model="gpt-3.5-turbo-0125",  # Modelo mais rápido
                temperature=0.7  # Temperatura padrão para conversas normais
            )

            # Aguardar a conclusão do run
            self._wait_for_run_completion(thread_id, run.id)

            # Obter a última mensagem (resposta do assistente)
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
            assistant_message = next(msg for msg in messages if msg.role == "assistant")
            response = assistant_message.content[0].text.value

            # Salvar mensagens no banco de dados
            from app.models import Message
            Message.create(thread_id, "user", message, chatbot_type=self.chatbot_type, user_name=user_name)
            Message.create(thread_id, "assistant", response, chatbot_type=self.chatbot_type)

            return {
                "response": response,
                "user_name": user_name
            }

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return {"error": str(e)}

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 12):
        start_time = time.time()
        polling_interval = 0.3  # Reduzido ainda mais
        max_retries = 3
        retries = 0
        
        while True:
            try:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                
                if run.status == "completed":
                    break
                elif run.status == "requires_action":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": "Processado"
                        })
                    
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                elif run.status == "failed":
                    logger.error(f"Run falhou com erro: {run.last_error}")
                    raise Exception(f"Run falhou: {run.last_error}")
                elif time.time() - start_time > timeout:
                    logger.error("Timeout ao aguardar resposta do assistente")
                    raise Exception("Timeout ao aguardar resposta do assistente")
                
                time.sleep(polling_interval)
                
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e
                time.sleep(0.5)  # Espera antes de tentar novamente

    def extract_name(self, message: str) -> Optional[str]:
        try:
            # Usar expressões regulares para tentar encontrar padrões comuns de nome
            patterns = [
                r"(?i)meu nome[^\w]*(é|eh)[^\w]*([a-zA-ZÀ-ÿ\s]+)",  # Adicionado \s para nomes compostos
                r"(?i)me chamo[^\w]*([a-zA-ZÀ-ÿ\s]+)",
                r"(?i)sou[^\w]*o[^\w]*([a-zA-ZÀ-ÿ\s]+)",
                r"(?i)sou[^\w]*a[^\w]*([a-zA-ZÀ-ÿ\s]+)",
                r"(?i)pode[^\w]*me[^\w]*chamar[^\w]*de[^\w]*([a-zA-ZÀ-ÿ\s]+)",
                r"(?i)^([a-zA-ZÀ-ÿ\s]+)$"  # Tenta extrair se a mensagem for apenas um nome
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    # Pega o último grupo de captura (o nome)
                    name = match.group(match.lastindex).strip().capitalize()
                    # Verifica se é um nome válido (mais de 2 caracteres e não é uma palavra comum)
                    if len(name) > 2 and not any(word.lower() in ["sou", "meu", "me", "eh", "é", "sim", "não", "nao"] for word in name.split()):
                        return name
            
            # Se não encontrou com regex, usa a OpenAI como fallback
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Extraia apenas o primeiro nome desta mensagem (responda APENAS o nome, sem pontuação ou texto adicional). Se não houver nome, responda apenas 'não'. Mensagem: {message}"
            )
            
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
                model="gpt-3.5-turbo-0125",
                temperature=0.2  # Temperatura mais baixa para maior precisão
            )
            
            self._wait_for_run_completion(thread.id, run.id, timeout=5)
            
            messages = client.beta.threads.messages.list(thread_id=thread.id, limit=1)
            assistant_message = next(msg for msg in messages if msg.role == "assistant")
            extracted_name = assistant_message.content[0].text.value.strip()
            
            client.beta.threads.delete(thread.id)
            
            if len(extracted_name) > 2 and extracted_name.lower() != "não":
                return extracted_name.capitalize()
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair nome: {str(e)}")
            return None

    def generate_summary(self, messages: List[Dict]) -> str:
        try:
            # Criar uma thread temporária para gerar o resumo
            thread = client.beta.threads.create()
            
            # Preparar o contexto para o assistente
            context = "Analise as seguintes mensagens do WhatsApp e gere um resumo detalhado:\n\n"
            for msg in messages:
                context += f"De: {msg.get('sender', 'Desconhecido')}\n"
                context += f"Mensagem: {msg.get('content', '')}\n"
                context += f"Data: {msg.get('timestamp', '')}\n\n"
            
            # Adicionar o contexto como mensagem do usuário
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=context
            )
            
            # Criar e executar o run
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Aguardar a conclusão
            self._wait_for_run_completion(thread.id, run.id)
            
            # Obter a resposta
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_message = next(msg for msg in messages if msg.role == "assistant")
            summary = assistant_message.content[0].text.value
            
            # Limpar a thread
            client.beta.threads.delete(thread.id)
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}")
            return f"Erro ao gerar resumo: {str(e)}"