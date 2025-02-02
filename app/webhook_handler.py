from flask import request, jsonify
from app import app  # Importe a instância do app do seu aplicativo principal
from .whatsapp_handler import process_whatsapp_message

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        
        # Verifique se a estrutura do dado recebido está correta
        if 'message' in data and 'text' in data['message']:
            message_text = data['message']['text']
            
            # Processe a mensagem usando a função existente
            response = process_whatsapp_message(message_text)
            
            # Aqui você pode adicionar lógica para enviar a resposta de volta ao WhatsApp
            # Por exemplo, usando a API da Evolution para enviar uma mensagem
            
            print("Mensagem processada:", message_text)
            print("Resposta:", response)
            
            return jsonify({"status": "success", "response": response}), 200
        else:
            return jsonify({"status": "error", "message": "Formato de mensagem inválido"}), 400
    
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
