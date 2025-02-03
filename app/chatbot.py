# Importações necessárias
from openai import OpenAI
from config import Config
import time
from typing import Optional, List, Dict

# Inicialização do cliente OpenAI com a chave API
client = OpenAI(api_key=Config.OPENAI_API_KEY)

class Chatbot:
    def __init__(self, chatbot_type: str):
        """
        Inicializa o chatbot com um tipo específico.
        Seleciona o ID do assistente apropriado com base no tipo de chatbot.
        """
        self.chatbot_type = chatbot_type
        if chatbot_type == "atual":
            self.assistant_id = Config.ASSISTANT_ID_VENDAS
        elif chatbot_type == "novo":
            self.assistant_id = Config.ASSISTANT_ID_TREINAMENTO
        elif chatbot_type == "whatsapp":
            self.assistant_id = Config.ASSISTANT_ID_WHATSAPP
        else:
            raise ValueError(f"Tipo de chatbot inválido: {chatbot_type}")

    def create_thread(self) -> str:
        """
        Cria uma nova thread de conversa e retorna seu ID.
        """
        thread = client.beta.threads.create()
        return thread.id

    def send_message(self, thread_id: str, message: str) -> str:
        """
        Envia uma mensagem para uma thread específica e retorna a resposta do assistente.
        Utiliza o assistente configurado para processar a mensagem.
        """
        # Adiciona a mensagem do usuário à thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        # Inicia uma execução do assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        # Aguarda a conclusão da execução
        self._wait_for_run_completion(thread_id, run.id)
        # Recupera e retorna a resposta do assistente
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        if messages.data and messages.data[0].content:
            return messages.data[0].content[0].text.value
        return "Desculpe, não foi possível gerar uma resposta."

    def extract_name(self, message: str) -> Optional[str]:
        """
        Tenta extrair um nome de uma mensagem usando um assistente especializado.
        Retorna o nome extraído ou None se nenhum nome for encontrado.
        """
        try:
            print(f"Tentando extrair nome da mensagem: '{message}'")
            temp_thread = self.create_thread()
            print(f"Thread temporária criada: {temp_thread}")
    
            # Configura o assistente com instruções específicas
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content="Você é um assistente especializado em extrair nomes de pessoas de mensagens. Se um nome for mencionado, retorne apenas o nome. Se nenhum nome for mencionado, retorne 'Nenhum nome encontrado'. Ignore palavras como 'sou', 'me chamo', etc. Retorne apenas o primeiro nome encontrado."
            )
    
            # Envia a mensagem para extração do nome
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content=f"Extraia o nome da pessoa desta mensagem: '{message}'"
            )
    
            # Executa o assistente e aguarda a resposta
            run = client.beta.threads.runs.create(
                thread_id=temp_thread,
                assistant_id=self.assistant_id
            )
            print(f"Run criada: {run.id}")
    
            self._wait_for_run_completion(temp_thread, run.id)
            print("Run completada")
    
            # Processa a resposta do assistente
            messages = client.beta.threads.messages.list(thread_id=temp_thread)
            if messages.data and messages.data[0].content:
                extracted_name = messages.data[0].content[0].text.value.strip()
                print(f"Nome extraído pelo assistente: '{extracted_name}'")
        
                if extracted_name.lower() == "nenhum nome encontrado":
                    print("Nenhum nome encontrado na mensagem")
                    return None
                else:
                    print(f"Nome extraído com sucesso: {extracted_name}")
                    return extracted_name
            else:
                print("Nenhuma resposta válida do assistente")
                return None
        except Exception as e:
            print(f"Erro ao extrair nome: {e}")
            return None

    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Gera um resumo formatado das mensagens do WhatsApp usando o modelo GPT-4.
        Retorna um resumo estruturado em HTML ou uma mensagem de erro.
        """
        try:
            print("Iniciando geração de resumo das mensagens do WhatsApp")
        
            # Instruções detalhadas para o modelo de linguagem
            system_message = """Você é um assistente especializado em monitorar e resumir conversas do WhatsApp. 
            Sua tarefa é analisar mensagens, identificar tópicos principais, e criar resumos concisos quando solicitado. 
            Mantenha a privacidade, não mencione nomes ou informações pessoais nos resumos.
        
            Formate o resumo da seguinte maneira:
            1. Comece com um breve resumo geral da conversa.
            2. Liste os principais tópicos discutidos.
            3. Destaque as tendências e insights importantes.
            4. Conclua com observações finais ou recomendações, se aplicável.
        
            Use marcadores HTML para estruturar o resumo:
            - Use <h3> para títulos de seções
            - Use <p> para parágrafos
            - Use <ul> e <li> para listas não ordenadas
            - Use <strong> para enfatizar pontos importantes"""
        
            # Prepara a mensagem do usuário com todas as mensagens do WhatsApp
            user_message = "Por favor, faça um resumo das seguintes mensagens do WhatsApp, seguindo o formato especificado:\n\n"
            for message in messages:
                user_message += f"Remetente: {message['sender_name']}\nConteúdo: {message['content']}\n\n"

            # Faz a chamada para o modelo GPT-4
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000
            )

            summary = response.choices[0].message.content
            print("Resumo gerado com sucesso")
            return summary

        except Exception as e:
            print(f"Erro ao gerar resumo: {e}")
            return f"Erro ao gerar resumo: {str(e)}"

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 30):
        """
        Aguarda a conclusão da execução do assistente, com um timeout.
        Lança exceções em caso de timeout ou falha na execução.
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("A execução do assistente excedeu o tempo limite.")

            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                raise RuntimeError(
                    f"A execução do assistente falhou: {run_status.last_error}"
                )
            time.sleep(1)