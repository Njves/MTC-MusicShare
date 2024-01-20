import datetime
import functools
import http
import json
import os
import uuid
from typing import Callable

from typing_extensions import List

import app.validation as validation

from email_validator import validate_email, EmailNotValidError
from flask import request, render_template, redirect, jsonify, url_for, current_app, send_from_directory, make_response, \
    Response
from flask_login import current_user, login_required, login_user
from flask_socketio import emit, join_room, leave_room, disconnect
from werkzeug.utils import secure_filename

from app import socketio, db
from app.chat import bp
from app.image_converter import compress_image
from app.models import Message, Room, Attachment, User


def update_last_seen(args) -> None:
    """
    Обновляет последнее посещение пользователя в базе данных
    :param args: кортеж из объекта приложения и пользовательского id
    """
    app, user_id = args
    with app.app_context():
        user = User.query.get(user_id)
        user.last_seen = datetime.datetime.utcnow()
        db.session.add(user)
        db.session.commit()


@bp.route('/search-message')
def search_messages() -> Response:
    """
    Осуществляет поиск по сообщениям с помощью SQL функции like
    Поиск происходит по тексту сообщения
    :return:
    """
    query = request.args.get('query')
    result = Message.query.filter(Message.text.like("%" + query + "%")).all()
    result = [message.to_dict() for message in result]
    return jsonify({'result': result})


@bp.route("/get-current-user", methods=['GET'])
@login_required
def get_current_user() -> (dict, int):
    """
    Return username from current server session
    :return:
    """
    if not current_user:
        return {'error': 'The user does not exist'}, http.HTTPStatus.NOT_FOUND.value

    return current_user.to_dict()


@bp.route('/user/<int:user_id>', methods=['PUT'])
@login_required
def edit_user(user_id: int) -> (dict, int):
    """
    Изменяет поля пользователя
    :param user_id: идентификатор пользователя
    :return: ошибка если данные не валидны, успех если данные валидны
    """
    user_json: dict = request.json

    user: User = User.query.get_or_404(user_id)
    if validation.user_same_name_valid(current_app._get_current_object(), user_json.get('username')):
        return {'error': 'The name is occupied'}, http.HTTPStatus.UNPROCESSABLE_ENTITY.value
    if user_json.get('username'):
        user.username = user_json['username']
    if user_json.get('color'):
        if not validation.color_valid(user_json.get('color')):
            return {'error': 'Invalid color'}, http.HTTPStatus.CONFLICT.value
        user.color = user_json.get('color')
    if email_json := user_json.get('email'):
        try:
            emailinfo = validate_email(email_json, check_deliverability=False)
            email = emailinfo.normalized
            user.email = email
        except EmailNotValidError as e:
            return {'error': 'Invalid email address'}, http.HTTPStatus.CONFLICT.value
    if user_json.get('password'):
        if validation.length_password_valid(user_json['password']):
            return {'error': 'The password must be more than 6 characters long'}, http.HTTPStatus.CONFLICT.value
    user.last_seen = datetime.datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201


@bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id: int) -> (dict, int):
    """
    Возвращает JSON пользователя
    :param user_id: идентификатор
    :return: ошибка если пользователь не найден, успех если найден
    """

    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return {'error': 'The user was not found'}, 404
    return user.to_dict()


@bp.route('/get-private-messages/<int:user_id>/<int:part>')
@login_required
def get_private_messages(user_id: int, part: int) -> (dict, int):
    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return {'error': 'The room was not found'}, http.HTTPStatus.NOT_FOUND.value
    if part <= 0:
        return {'error': 'Unsupported value'}, http.HTTPStatus.BAD_REQUEST.value
    user_dict: dict = user.to_dict()
    user_dict['messages']: List[Message] = [message.to_dict() for message in user.received_messages[
                                                              (part - 1) * current_app.config['MESSAGE_PART']:
                                                              part * current_app.config['MESSAGE_PART']][::-1]]
    return user_dict, 200


@bp.route("/get-rooms")
@login_required
def get_rooms() -> Response:
    """
    Возвращает текущие комнаты
    :return: Текущие комнаты
    """
    rooms: List[Room] = [room.to_dict() for room in Room.query.all()]
    response: Response = jsonify(rooms)
    print(response.json)
    # response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route('/get-missed-messages', methods=['GET'])
@login_required
def get_missed_message() -> Response:
    """
    Возвращает непрочитанные сообщения пользователем
    :return: непрочитаннеы сообщения пользователем
    """
    missed_messages: List[Message] = Message.query.where(Message.date > current_user.last_seen).all()
    missed_messages = [message.to_dict() for message in missed_messages]
    socketio.start_background_task(update_last_seen, (current_app._get_current_object(), current_user.id,))
    return jsonify(missed_messages)


@bp.route("/create-room", methods=['POST'])
@login_required
def create_room() -> (dict, int):
    """
    Создает новую комнату и возвращает её
    :return: JSON представление новой комнаты
    """
    room_json = request.json
    new_room = Room.from_dict(room_json)
    db.session.add(new_room)
    db.session.commit()
    socketio.emit('new_room', new_room.to_dict())
    return new_room.to_dict(), 201


@bp.route("/get-notify-message", methods=['GET'])
def get_notify() -> Response:
    """
    Возвращает звук уведомления
    :return: .mp3 файл звука уведомления
    """
    return send_from_directory('static/sound', 'msg_notify.mp3')


@bp.route("/get-room/<int:room_id>", methods=['GET'])
@login_required
def get_history_by_room_name(room_id: int) -> (dict, int):
    """
    Возвращает часть историю сообщений в комнате
    :param room_id: идентификатор комнаты
    :param part: часть по 50 сообщений
    :return: ошибка в случае неудачи, json комнаты с сообщениями
    """
    count = request.args.get('count') if request.args.get('count') else 100
    offset = request.args.get('offset') if request.args.get('offset') else 0
    room: Room = Room.query.filter_by(id=room_id).first()
    if not room:
        return {'error': 'The room was not found'}, http.HTTPStatus.NOT_FOUND.value
    room_dict = room.to_dict()
    room_dict['messages'] = room.messages[offset: offset + count]
    response = jsonify(room_dict)
    response.delete_cookie('current_room')
    response.set_cookie('current_room', f'{room.id}', 60 * 60 * 24 * 30)
    response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route("/get-online", methods=['GET'])
@login_required
def get_users_online() -> Response:
    """
    Возвращает текущих пользователей в socket сессии
    :return:
    """
    return jsonify([user.to_dict() for user in users.keys()])


@bp.route("/attach", methods=['POST'])
@login_required
def attach() -> (dict, int):
    """
    Создает сообщение с прикрепленным медиа файлом (музыка, изображение)
    :return: JSON объект сообщения с attachment
    """
    if 'attach_file' not in request.files:
        return {'error': 'The file is not attached'}, http.HTTPStatus.BAD_REQUEST.value
    file = request.files.get('attach_file')
    if file.filename == '':
        return {'error': 'The file name is missing'}, http.HTTPStatus.BAD_REQUEST.value
    user_filename = secure_filename(file.filename)
    filename, ext = user_filename.rsplit('.')
    filename = f'{filename}_${uuid.uuid4()}.png'
    text = request.form.get('text')
    room_id = request.form.get('room_id')
    if not text:
        text = ''
    link = os.path.join(os.path.join('app', current_app.config['UPLOAD_FOLDER']), filename)
    file.save(link)
    if 'image' in file.content_type:
        compress_image(link)
    link = url_for('chat.get_content', name=filename)
    message = Message(user_id=current_user.id, text=text, date=datetime.datetime.utcnow(), room_id=room_id)
    attachment = Attachment(type=file.content_type, link=link)
    message.attachments.append(attachment)
    db.session.add(attachment)
    db.session.add(message)
    db.session.commit()
    socketio.emit('chat', message.to_dict())
    return message.to_dict(), 201


@bp.route('/message/<int:msg_id>', methods=['DELETE'])
@login_required
def remove_message(msg_id: int) -> (dict, int):
    """
    Удаляет сообщение
    :param msg_id: идентификатор сообщения
    :return: ошибка в случае неудачи, пустое тело в случае удачи
    """
    message: Message = Message.query.filter_by(id=msg_id).first()
    if not message:
        return {'error': 'The message was not found'}, http.HTTPStatus.NOT_FOUND.value
    if current_user.id != message.user.id:
        return {'error': 'The user is not the sender of the message'}, http.HTTPStatus.FORBIDDEN.value
    db.session.delete(message)
    db.session.commit()
    return {}, 204


@bp.route('/message/<int:msg_id>', methods=['PUT'])
@login_required
def edit_message(msg_id: int) -> (dict, int):
    """
    Редактирует сообщение
    :param msg_id: идентификатор сообщения
    :return: JSON измененного сообщение
    """
    old_message = Message.query.filter_by(id=msg_id).first()
    if current_user.id != old_message.user.id:
        return {'error': 'The user is not the sender of the message'}, http.HTTPStatus.FORBIDDEN.value
    old_message.text = request.json.get('text')
    old_message.room_id = request.json.get('room_id')
    old_message.attachments = request.json.get('attachments')
    if not old_message:
        return {'error': 'The message was not found'}, http.HTTPStatus.NOT_FOUND.value
    db.session.commit()
    return old_message.to_dict(), 201


@bp.route('/get-content/<path:name>', methods=['GET'])
@login_required
def get_content(name) -> Response:
    """
    Возвращает медиа файл
    :param name: название медиа файла
    :return: медиа файл
    """
    response = send_from_directory(current_app.config['UPLOAD_FOLDER'], name)
    response.headers['Cache-Control'] = 'public,max-age=300'
    return response


