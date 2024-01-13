from flask import Blueprint
import os

bp = Blueprint('chat', __name__)


from app.chat import routes
