from flask import Blueprint

bp = Blueprint('chat_socket', __name__)


from app.chat_socket import routes
