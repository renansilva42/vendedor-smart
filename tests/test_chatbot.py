# tests/test_chatbot.py
import unittest
from unittest.mock import patch, MagicMock
from app.chatbot.vendas import VendasChatbot
from app.chatbot.whatsapp import WhatsAppChatbot

class TestVendasChatbot(unittest.TestCase):
    @patch('app.chatbot.vendas.client')
    def test_query_whatsapp_data(self, mock_client):
        # Configurar mock
        mock_supabase = MagicMock()
        mock_query = MagicMock()
        mock_query.execute.return_value.data = [
            {"sender_name": "Test User", "content": "Hello", "timestamp": "2023-01-01T12:00:00"}
        ]
        mock_supabase.table.return_value.select.return_value = mock_query
        
        # Injetar mock
        with patch('app.chatbot.vendas.supabase', mock_supabase):
            chatbot = VendasChatbot()
            result = chatbot._query_whatsapp_data({"sender_name": "Test"})
            
            # Verificar resultado
            self.assertIn("success", result)
            self.assertIn("data", result)

class TestWhatsAppChatbot(unittest.TestCase):
    @patch('app.chatbot.whatsapp.client')
    def test_extract_name(self, mock_client):
        # Configurar mock
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "John"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Testar extração de nome
        chatbot = WhatsAppChatbot()
        name = chatbot.extract_name("Hello, my name is John")
        
        self.assertEqual(name, "John")
        
        # Testar cache
        chatbot._name_cache = {"Hello": "Jane"}
        name = chatbot.extract_name("Hello")
        self.assertEqual(name, "Jane")

if __name__ == '__main__':
    unittest.main()