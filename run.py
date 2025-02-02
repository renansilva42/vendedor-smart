from app import create_app
from app.models import supabase
import sys

# Teste de conexão com o Supabase
try:
    response = supabase.table('usuarios_chatbot').select('*').limit(1).execute()
    print("Conexão com Supabase bem-sucedida!")
    print(f"Resposta: {response}")
except Exception as e:
    print(f"Erro ao conectar com Supabase: {e}", file=sys.stderr)
    sys.exit(1)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)