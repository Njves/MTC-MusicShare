import http
from typing import List

from flask import Response, redirect, url_for, render_template, request, session
from flask_login import current_user, login_required

from app import db
from app.chat_socket.routes import users
from app.models import Room, Message
from app.site import bp


@bp.route("/", methods=['GET'])
def enter() -> Response:
    """
    Главаня страница входа
    :return:
    """
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('site.index'))


@bp.route("/site", methods=['GET'])
@login_required
def index() -> str | Response:
    """
    Возвращает html страницу чата
    :return:
    """
    rooms: List[Room] = Room.query.all()
    if current_room := request.args.get('room'):
        user_room = Room.query.filter_by(name=current_room).first()
        user_room.messages = user_room.messages[::-1]
        session['room_id'] = user_room.id
        if not user_room:
            return redirect(url_for('site.index'))
        return render_template('site/index.html', rooms=rooms, current_room=user_room, all_users=users)
    if session.get('room_id'):
        session.pop('room_id')
    return render_template('site/index.html', rooms=rooms, all_users=users)