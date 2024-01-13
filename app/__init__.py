import shutil
import os
import flask_socketio
from flask import Flask
from flask_admin import Admin
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

from config import Config

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

migrate = Migrate()
admin_app = Admin(name='MusicShare', template_mode='bootstrap3')
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))
socketio = flask_socketio.SocketIO()
login_manager = LoginManager()
cache = Cache()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    migrate.init_app(app, db, render_as_batch=True)
    db.init_app(app)
    admin_app.init_app(app)
    socketio.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    register_commands(app)
    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    return app


def register_commands(app):
    @app.cli.command('clear-content')
    def clear():
        """ Удаляет все картинки """
        if os.path.exists(f'./app/{app.config["UPLOAD_FOLDER"]}'):
            shutil.rmtree(f'./app/{app.config["UPLOAD_FOLDER"]}')
            os.mkdir('./app/content/')


from app import models, admin, cache
