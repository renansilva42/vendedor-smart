# app/utils/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app_name="vendedor-smart", log_level=logging.INFO):
    """Configura logging centralizado para a aplicação."""
    # Criar diretório de logs se não existir
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Configurar logger raiz
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Limpar handlers existentes
    if logger.handlers:
        logger.handlers.clear()
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        f"{log_dir}/{app_name}.log",
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger