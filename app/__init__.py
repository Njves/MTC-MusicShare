import flask_socketio
from flask import Flask, redirect, url_for
from flask_caching import Cache
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from config import Config
from flask_cors import CORS
migrate = Migrate()
db = SQLAlchemy()
socketio = flask_socketio.SocketIO(manage_session=False, cors_allowed_origins="*")
login_manager = LoginManager()
cache = Cache()
moment = Moment()


class FlaskAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return current_user.is_authenticated
        return super(FlaskAdminIndexView, self).index()


admin_app = Admin(index_view=FlaskAdminIndexView(), template_mode='bootstrap4')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    migrate.init_app(app, db, render_as_batch=True)
    db.init_app(app)
    socketio.init_app(app, engineio_logger=True)
    cache.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    moment.init_app(app)
    admin_app.init_app(app)
    CORS(app, supports_credentials=True)
    with app.app_context():
        from . import cli
    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    from app.site import bp as site_bp
    app.register_blueprint(site_bp)
    from app.chat_socket import bp as chat_socket
    app.register_blueprint(chat_socket)
    return app


from app import models, validation, admin
