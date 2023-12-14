from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_bootstrap import Bootstrap
# from config import Config
from flask_apscheduler import APScheduler

bootstrap = Bootstrap()
db = SQLAlchemy()
scheduler = APScheduler()

def create_app():
    app = Flask(__name__)
    # app.config.from_object(config_class)

    # Heroku environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['CLIENT_ID'] = os.environ.get('CLIENT_ID')
    app.config['CLIENT_SECRET'] = os.environ.get('CLIENT_SECRET')
    app.config['REDIRECT_URI'] = os.environ.get('REDIRECT_URI')
    app.config['SCOPE'] = os.environ.get('SCOPE')
    app.config['AUTO_UPDATE_CODE'] = os.environ.get('AUTO_UPDATE_CODE')
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['LOG_TO_STDOUT'] = os.environ.get('LOG_TO_STDOUT')
    
    bootstrap.init_app(app)
    db.init_app(app)

    scheduler.init_app(app)
    # task scheduling
    from app.models import Users
    # @scheduler.task('interval', id='update_playlists', seconds=60, misfire_grace_time=900)
    # # def job1():
    # #     print('Job 1 executed')
    @scheduler.task('cron', id='update_playlists', hour='6', day_of_week='mon-sun')
    def update_playlists_task():
        with app.app_context():
            Users.update_playlists()
    scheduler.start()

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
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