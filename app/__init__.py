from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Carregar configurações
    app.config.from_object(Config)
    
    # Registrar blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app 