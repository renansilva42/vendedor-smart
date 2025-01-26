from openai import OpenAI
from config import Config
import time
from typing import Optional

client = OpenAI(api_key=Config.OPENAI_API_KEY)

class Chatbot:
    def __init__(self, chatbot_type: str):
        if chatbot_type == "atual":
            self.assistant_id = Config.ASSISTANT_ID_VENDAS
        elif chatbot_type == "novo":
            self.assistant_id = Config.ASSISTANT_ID_TREINAMENTO
        else:
            raise ValueError(f"Tipo de chatbot inválido: {chatbot_type}")

    def create_thread(self) -> str:
        # Método para criar uma nova thread
        thread = client.beta.threads.create()
        return thread.id

    def send_message(self, thread_id: str, message: str) -> str:
        # Envia uma mensagem e retorna a resposta do assistente
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        self._wait_for_run_completion(thread_id, run.id)
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        if messages.data and messages.data[0].content:
            return messages.data[0].content[0].text.value
        return "Desculpe, não foi possível gerar uma resposta."

    def extract_name(self, message: str) -> Optional[str]:
        try:
            print(f"Tentando extrair nome da mensagem: '{message}'")
            temp_thread = self.create_thread()
            print(f"Thread temporária criada: {temp_thread}")
    
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content="Você é um assistente especializado em extrair nomes de pessoas de mensagens. Se um nome for mencionado, retorne apenas o nome. Se nenhum nome for mencionado, retorne 'Nenhum nome encontrado'. Ignore palavras como 'sou', 'me chamo', etc."
            )
    
            client.beta.threads.messages.create(
                thread_id=temp_thread,
                role="user",
                content=f"Extraia o nome da pessoa desta mensagem: '{message}'"
            )
    
            run = client.beta.threads.runs.create(
                thread_id=temp_thread,
                assistant_id=self.assistant_id
            )
            print(f"Run criada: {run.id}")
    
            self._wait_for_run_completion(temp_thread, run.id)
            print("Run completada")
    
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

    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 30):
        # Aguarda a conclusão da execução do assistente
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
