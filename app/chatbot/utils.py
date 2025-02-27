# app/chatbot/utils.py
import logging
import json
from typing import Dict, List, Any, Optional
import datetime

logger = logging.getLogger("chatbot.utils")

def format_timestamp(timestamp) -> str:
    """Converte diferentes formatos de timestamp para ISO 8601."""
    try:
        if isinstance(timestamp, str):
            if timestamp.replace('.', '').isdigit():
                # Se for um timestamp Unix como string
                timestamp_float = float(timestamp)
                return datetime.datetime.fromtimestamp(timestamp_float).isoformat()
            else:
                # Tentar analisar como string de data
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    return dt.isoformat()
                except ValueError:
                    pass
        
        # Usar o timestamp atual se não for válido
        return datetime.datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Erro ao formatar timestamp: {str(e)}")
        return datetime.datetime.now().isoformat()

def sanitize_content(content: str) -> str:
    """Sanitiza o conteúdo para armazenamento seguro."""
    if not content:
        return ""
    
    # Limitar tamanho
    if len(content) > 10000:
        content = content[:10000] + "... (truncado)"
    
    # Remover caracteres potencialmente problemáticos
    return content.replace("\0", "")

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extrai entidades do texto usando regras simples."""
    entities = {
        "pessoas": [],
        "organizações": [],
        "locais": [],
        "datas": []
    }
    
    # Implementação simplificada - em produção, usar NER
    words = text.split()
    for word in words:
        if word.startswith("@"):
            entities["pessoas"].append(word[1:])
        elif word.startswith("#"):
            entities["organizações"].append(word[1:])
    
    return entities