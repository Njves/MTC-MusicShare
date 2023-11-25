from flask import Blueprint

bp = Blueprint('room', __name__)

from app.auth import routes
