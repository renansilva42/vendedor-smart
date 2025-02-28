# docs/generate_docs.py
import os
import sys
import inspect
import importlib
import markdown

def generate_module_docs(module_name, output_dir="docs/api"):
    """Gera documentação para um módulo Python."""
    try:
        # Importar o módulo
        module = importlib.import_module(module_name)
        
        # Criar diretório de saída se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Nome do arquivo de saída
        output_file = os.path.join(output_dir, f"{module_name.replace('.', '_')}.md")
        
        with open(output_file, 'w') as f:
            # Escrever cabeçalho
            f.write(f"# {module_name}\n\n")
            
            # Documentação do módulo
            if module.__doc__:
                f.write(f"{module.__doc__}\n\n")
                
            # Listar classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name:
                    f.write(f"## Class: {name}\n\n")
                    
                    # Documentação da classe
                    if obj.__doc__:
                        f.write(f"{obj.__doc__}\n\n")
                        
                    # Listar métodos
                    for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                        if not method_name.startswith('_') or method_name == '__init__':
                            f.write(f"### {method_name}\n\n")
                            
                            # Documentação do método
                            if method.__doc__:
                                f.write(f"{method.__doc__}\n\n")
                                
                            # Assinatura do método
                            signature = inspect.signature(method)
                            f.write(f"```python\n{method_name}{signature}\n```\n\n")
            
            # Listar funções
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if obj.__module__ == module_name:
                    f.write(f"## Function: {name}\n\n")
                    
                    # Documentação da função
                    if obj.__doc__:
                        f.write(f"{obj.__doc__}\n\n")
                        
                    # Assinatura da função
                    signature = inspect.signature(obj)
                    f.write(f"```python\n{name}{signature}\n```\n\n")
        
        print(f"Documentação gerada para {module_name} em {output_file}")
        return output_file
    except Exception as e:
        print(f"Erro ao gerar documentação para {module_name}: {e}")
        return None

def generate_html_docs(markdown_file, output_dir="docs/html"):
    """Converte documentação Markdown para HTML."""
    try:
        # Criar diretório de saída se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Nome do arquivo de saída
        output_file = os.path.join(
            output_dir, 
            os.path.basename(markdown_file).replace('.md', '.html')
        )
        
        # Ler conteúdo Markdown
        with open(markdown_file, 'r') as f:
            md_content = f.read()
            
        # Converter para HTML
        html_content = markdown.markdown(
            md_content, 
            extensions=['fenced_code', 'codehilite']
        )
        
        # Adicionar estilo básico
        html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{os.path.basename(markdown_file)}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                code {{ font-family: monospace; }}
                h1, h2, h3 {{ color: #333; }}
                h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Escrever arquivo HTML
        with open(output_file, 'w') as f:
            f.write(html_doc)
            
        print(f"Documentação HTML gerada em {output_file}")
        return output_file
    except Exception as e:
        print(f"Erro ao gerar HTML para {markdown_file}: {e}")
        return None

if __name__ == "__main__":
    # Adicionar diretório raiz ao path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Módulos para documentar
    modules = [
        'app.chatbot.base',
        'app.chatbot.vendas',
        'app.chatbot.whatsapp',
        'app.chatbot.treinamento',
        'app.models',
        'app.routes'
    ]
    
    # Gerar documentação para cada módulo
    for module in modules:
        md_file = generate_module_docs(module)
        if md_file:
            generate_html_docs(md_file)