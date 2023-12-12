from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_bootstrap import Bootstrap
from config import Config

bootstrap = Bootstrap()
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    bootstrap.init_app(app)
    db.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')

            file_handler = RotatingFileHandler('logs/cafegram.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('Cafegram startup')

    return app

from app import models