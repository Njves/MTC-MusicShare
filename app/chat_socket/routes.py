import functools
import json
from datetime import datetime
from typing import Callable
from flask import request, current_app, jsonify
from flask_login import login_user, current_user, login_required
from flask_socketio import disconnect, emit, leave_room, join_room

from app import socketio, db
from app.models import User, Message, Room, Attachment
from app.chat_socket import bp

users: dict[User, int] = {}
geo: dict[User, dict] = {}
rooms = {}


@bp.route('/room/<int:room_id>/geo')
@login_required
def get_users_geo(room_id):
    response = {}
    user2 = User.query.filter_by(username='admin1').first()
    user1 = User.query.filter_by(username='Egor').first()
    rooms[1] = [user2, user1]
    geo[user1] = {'lat': 55, 'lon': 55, 'username': user1.username}
    geo[user2] = {'lat': 54, 'lon': 51, 'username': user2.username}
    if room_id not in rooms:
        return {}, 40
    response['users'] = []
    for user in rooms[room_id]:
        response['users'].append(geo[user])
    return jsonify(response)


@bp.route("/user/geo", methods=['POST'])
@login_required
def push_geo() -> (dict, int):
    """
    Return
    """
    geo[current_user._get_current_object()] = {'lat': request.json.get('lat'), 'lon': request.json.get('lon')}
    return current_user.to_dict()


@bp.route("/user/room", methods=['POST'])
@login_required
def put_user_room() -> (dict, int):
    """
    Return
    """
    save_room(request.json.get('room_id'))
    return current_user.to_dict()


def save_room(room_id):
    print(room_id)
    if room_id not in rooms:
        rooms[room_id] = [current_user._get_current_object()]
    else:
        rooms[room_id].append(current_user._get_current_object())


def authenticated_only(f: Callable) -> Callable:
    """
    Декоратор для авторизации с помощью socketio
    :param f: оборачиваемая функция
    :return: записываем пользователя в сессию иначе отключаем сокет
    """

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        token = request.args.get('token')
        print(token)
        if token is None:
            disconnect()
        else:
            if User.verify_token(token) is None:
                current_app.logger.debug('Неудалось подтянуть пользователя', token)
                disconnect()
            login_user(User.verify_token(token), remember=True)
            return f(*args, **kwargs)

    return wrapped


@socketio.on("connect")
@authenticated_only
def handle_connect():
    """
    Connect событие для сокета
    """
    users[current_user._get_current_object()] = request.sid
    emit('join', current_user.to_dict(), broadcast=True)


@socketio.on('push_geo')
@authenticated_only
def push_geo(data: dict | str):
    """
    Получает на вход lon и lan
    :param data:
    :return:
    """
    print(data)
    if isinstance(data, str):
        data = json.loads(data)
    geo[current_user._get_current_object()] = {'lat': data.get('lan'), 'lon': data.get('lon'), 'username': current_user.usename}


@socketio.on("join")
@authenticated_only
def on_join(data: dict | str):
    """
    Событие входа, помещает пользователя в комнату
    :param data: JSON с идентификатором комнаты
    """
    if isinstance(data, str):
        data = json.loads(data)
    room_id = data.get('id')
    if not room_id:
        socketio.emit('exception', {'error': 'The room ID is missing'})
    if not Room.is_exists(room_id):
        socketio.emit('exception', {'error': 'There is no room with this ID'})
    save_room(room_id)
    join_room(room_id)


@socketio.on("leave")
@authenticated_only
def on_join(data: dict | str):
    if isinstance(data, str):
        data = json.loads(data)
    room_id = data['id']
    if not room_id:
        socketio.emit('exception', {'error': 'The room ID is missing'})
    if not Room.is_exists(room_id):
        socketio.emit('exception', {'error': 'There is no room with this ID'})
    print(current_user.username, 'leaved to', data['id'], 'room')
    del geo[current_user._get_current_object()]
    for key, value in rooms.items():
        if value == current_user:
            del rooms[key]
    leave_room(room_id)


@socketio.on("delete")
@authenticated_only
def on_join(data: dict | str):
    """
    Событие вызываемое при удаление данных, например сообщения
    Отправляет событие "on_delete" клиенту
    :param data: JSON представления объекта
    """
    if isinstance(data, str):
        data = json.loads(data)
    socketio.emit('on_delete', data)


@socketio.on("disconnect")
@authenticated_only
def handle_user_leave():
    """
    Событие отключения пользователя из сокет сессии
    Отправляет всем пользователям из сокет сессии сообщение
    "leave" с объектом пользователяt
    """
    leaved_user: User = None
    for user in users:
        if request.sid == users.get(user):
            leaved_user = user
            break
    if leaved_user:
        del users[leaved_user]
        leaved_user.last_seen = datetime.utcnow()
        db.session.commit()
        emit('leave', leaved_user.to_dict(), broadcast=True)


@socketio.on("new_message")
@authenticated_only
def handle_new_message(message):
    """
    Событие нового сообщения в комнате
    При вызове отправляет событие chat с объектом сообщения в формате JSON
    Отправляет событие notify всем пользователям в текущей сессии
    :param message: JSON представление с room_id, где room_id идентификатор комнаты
    """
    msg = message
    if not isinstance(message, dict):
        msg = json.loads(message)

    if not msg['text'] and not msg['attachments']:
        return
    if not msg['room_id']:
        return

    attachments = [Attachment(link=attachment['link'], type=attachment['type']) for attachment in msg['attachments']]
    current_app.logger.debug('Отправленное сообщение', message)
    message = Message(user=current_user, text=msg['text'], date=datetime.utcnow(), room_id=msg['room_id'],
                      attachments=attachments)
    db.session.add(message)
    db.session.commit()
    print('new_message', message.to_dict())
    emit("chat", message.to_dict(), to=message.room_id)
    if not message.is_private():
        room = Room.query.filter_by(id=msg['room_id']).first()
        for sub in room.subscribers:
            pass
        emit("notify", message.to_dict(), broadcast=True)


@socketio.on("private_message")
@authenticated_only
def handle_private_message(message: dict | str):
    """
    Событие нового сообщения пользователю
    При вызове отправляет событие chat с объектом сообщения в формате JSON
    Отправляет событие notify всем пользователям в текущей сессии
    :param message: JSON представление с room_id, где room_id идентификатор комнаты
    """
    msg: dict = message
    if not isinstance(message, dict):
        msg = json.loads(message)
    if not msg['text']:
        return
    user_id = msg['user_id']
    receiver = User.query.filter_by(id=user_id).first()
    if not receiver:
        return
    message = Message(user=current_user, text=msg['text'], date=datetime.datetime.utcnow(),
                      receiver=user_id, user_id=current_user.id)
    emit("private", message.to_dict(), to=receiver)
    print('private_message', message.to_dict())
    db.session.add(message)
    db.session.commit()
