import unittest
import sys
import os
from supabase import create_client

# Adjust the path to import config.py correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

class TestSupabaseConnection(unittest.TestCase):
    def setUp(self):
        self.supabase_url = Config.SUPABASE_URL
        self.supabase_key = Config.SUPABASE_KEY
        self.client = create_client(self.supabase_url, self.supabase_key)

    def test_connection(self):
        try:
            response = self.client.table('usuarios_chatbot').select('*').limit(1).execute()
            self.assertIsNotNone(response)
            self.assertFalse(hasattr(response, 'error') and response.error)
            print("Supabase connection test passed.")
        except Exception as e:
            self.fail(f"Supabase connection test failed: {e}")

if __name__ == '__main__':
    unittest.main()
