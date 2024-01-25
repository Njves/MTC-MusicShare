import http
from typing import List

from flask import Response, redirect, url_for, render_template, request, session
from flask_login import current_user, login_required

from app import db
from app.chat_socket.routes import users
from app.models import Room, Message
from app.site import bp


@bp.route("/favorite", methods=['GET'])
def enter() -> Response:
    """
    Главаня страница входа
    :return:
    """
    return render_template('site/index.html')