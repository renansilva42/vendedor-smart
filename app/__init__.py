from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    from app.routes import bp  # Importar o Blueprint corretamente
    app.register_blueprint(bp)  # Registrar o Blueprint

    return app