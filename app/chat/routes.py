import datetime
import functools
import http
import json
import os
import re
import uuid

from email_validator import validate_email, EmailNotValidError
from flask import request, render_template, redirect, jsonify, url_for, current_app, send_from_directory, make_response
from flask_login import current_user, login_required, login_user
from flask_socketio import emit, join_room, leave_room, disconnect
from werkzeug.utils import secure_filename

from app import socketio, db
from app.chat import bp
from app.image_converter import compress_image
from app.models import Message, Room, Attachment, User

# from app.cache import cache_html, cache_rooms
users = {}


def authenticated_only(f):
    """
    Декоратор для авторизации с помощью socketio
    :param f: оборачиваемая функция
    :return: записываем пользователя в сессию иначе отключаем сокет
    """

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        user_id = request.args.get('user_id')
        if user_id is None:
            disconnect()
        else:
            login_user(User.query.get(user_id), remember=True)
            return f(*args, **kwargs)

    return wrapped


def update_last_seen(args):
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


@bp.route("/", methods=['GET'])
def enter():
    """
    Главаня страница входа
    :return:
    """
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('chat.index'))


@bp.route('/search-message')
def search_messages():
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
def get_current_user():
    """
    Return username from current server session
    :return:
    """
    if not current_user:
        response = jsonify({'error': 'Пользователя не существует'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    return current_user.to_dict()


@bp.route('/user/<int:user_id>', methods=['PUT'])
@login_required
def edit_user(user_id):
    """
    Изменяет поля пользователя
    :param user_id: идентификатор пользователя
    :return: ошибка если данные не валидны, успех если данные валидны
    """
    user_json = request.json
    user = User.query.get(user_id)
    if User.query.filter_by(username=user_json.get('username')).first():
        response = jsonify({'error': 'Имя занято'})
        response.status_code = http.HTTPStatus.CONFLICT.value
        return response
    if user_json.get('username'):
        user.username = user_json['username']
    print(user_json.get('color'))
    if user_json.get('color'):
        if not re.match('^#(?:[0-9a-fA-F]{3}){1,2}$', user_json.get('color')):
            response = jsonify({'error': 'Не валидный цвет'})
            response.status_code = http.HTTPStatus.CONFLICT.value
            return response
        user.color = user_json.get('color')
    if email_json := user_json.get('email'):
        try:
            emailinfo = validate_email(email_json, check_deliverability=False)
            email = emailinfo.normalized
            user.email = email
        except EmailNotValidError as e:
            response = jsonify({'error': e})
            response.status_code = http.HTTPStatus.CONFLICT.value
            return response
    if user_json.get('password'):
        if not user.set_password(user_json['password']):
            response = jsonify({'error': 'Пароль должен быть больше 6 символов'})
            response.status_code = http.HTTPStatus.CONFLICT.value
            return response
    user.last_seen = datetime.datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201


@bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """
    Возвращает JSON пользователя
    :param user_id: идентификатор
    :return: ошибка если пользователь не найден, успех если найден
    """
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return {'error': 'Пользователь не найден'}, 404
    return user.to_dict()


@bp.route('/get-private-messages/<int:user_id>/<int:part>')
def get_private_messages(user_id, part):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        response = jsonify({'error': 'Комната не найдена'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    if part <= 0:
        response = jsonify({'error': 'Непподержимовое значение'})
        response.status_code = http.HTTPStatus.BAD_REQUEST.value
        return response
    user_dict = user.to_dict()
    user_dict['messages'] = [message.to_dict() for message in user.received_messages[
                                                              (part - 1) * current_app.config['MESSAGE_PART']:
                                                              part * current_app.config['MESSAGE_PART']][::-1]]
    return user_dict, 200


@bp.route("/get-rooms")
@login_required
def get_rooms():
    """
    Возвращает текущие комнаты
    :return: Текущие комнаты
    """
    rooms = [room.to_dict() for room in Room.query.all()]
    response = jsonify({'rooms': rooms})
    # response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route('/get-missed-messages', methods=['GET'])
@login_required
def get_missed_message():
    """
    Возвращает непрочитанные сообщения пользователем
    :return: непрочитаннеы сообщения пользователем
    """
    missed_messages = Message.query.where(Message.date > current_user.last_seen).all()
    missed_messages = [message.to_dict() for message in missed_messages]
    socketio.start_background_task(update_last_seen, (current_app._get_current_object(), current_user.id,))
    return jsonify(missed_messages)


@bp.route("/create-room", methods=['POST'])
@login_required
def create_room():
    """
    Создает новую комнату и возвращает её
    :return: JSON представление новой комнаты
    """
    room_name = request.json.get('room_name')
    new_room = Room(name=room_name)
    db.session.add(new_room)
    db.session.commit()
    socketio.emit('new_room', {'room': new_room.to_dict()})
    return {'room': new_room.to_dict()}, 201


@bp.route("/get-notify-message", methods=['GET'])
def get_notify():
    """
    Возвращает звук уведомления
    :return: .mp3 файл звука уведомления
    """
    return send_from_directory('static/sound', 'msg_notify.mp3')


@bp.route("/chat", methods=['GET'])
@login_required
def index():
    """
    Возвращает html страницу чата
    :return:
    """
    return render_template('chat/index.html')


@bp.route("/get-room/<int:room_id>/<int:part>", methods=['GET'])
@login_required
def get_history_by_room_name(room_id, part):
    """
    Возвращает часть историю сообщений в комнате
    :param room_id: идентификатор комнаты
    :param part: часть по 50 сообщений
    :return: ошибка в случае неудачи, json комнаты с сообщениями
    """
    room = Room.query.filter_by(id=room_id).first()
    if part <= 0:
        response = jsonify({'error': 'Непподержимовое значение'})
        response.status_code = http.HTTPStatus.BAD_REQUEST.value
        return response
    if not room:
        response = jsonify({'error': 'Комната не найдена'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    room_dict = room.to_dict()
    room_dict['messages'] = [message.to_dict() for message in room.messages[
                                                              (part - 1) * current_app.config['MESSAGE_PART']:
                                                              part * current_app.config['MESSAGE_PART']][::-1]]
    response = jsonify(room_dict)
    response.delete_cookie('current_room')
    response.set_cookie('current_room', f'{room.id}', 60 * 60 * 24 * 30)
    response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route("/get-online", methods=['GET'])
@login_required
def get_users_online():
    """
    Возвращает текущих пользователей в socket сессии
    :return:
    """
    return jsonify([user.to_dict() for user in users.keys()])


@bp.route("/attach", methods=['POST'])
@login_required
def attach():
    """
    Создает сообщение с прикрепленным медиа файлом (музыка, изображение)
    :return: JSON объект сообщения с attachment
    """
    if 'attach_file' not in request.files:
        response = jsonify({'error': 'Файл не прикреплен'})
        response.status_code = http.HTTPStatus.BAD_REQUEST.value
        return response
    file = request.files.get('attach_file')
    if file.filename == '':
        response = jsonify({'error': 'Отсуствует имя файла'})
        response.status_code = http.HTTPStatus.BAD_REQUEST.value
        return response
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
def remove_message(msg_id):
    """
    Удаляет сообщение
    :param msg_id: идентификатор сообщения
    :return: ошибка в случае неудачи, пустое тело в случае удачи
    """
    message = Message.query.filter_by(id=msg_id).first()
    if not message:
        response = jsonify({'error': 'Сообщение не найдено'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    if current_user.id != message.user.id:
        response = jsonify({'error': 'Пользователь не является отправителем сообщения'})
        response.status_code = http.HTTPStatus.FORBIDDEN.value
        return response
    db.session.delete(message)
    db.session.commit()
    return {}, 204


@bp.route('/message/<int:msg_id>', methods=['PUT'])
@login_required
def edit_message(msg_id):
    """
    Редактирует сообщение
    :param msg_id: идентификатор сообщения
    :return: JSON измененного сообщение
    """
    old_message = Message.query.filter_by(id=msg_id).first()
    if current_user.id != old_message.user.id:
        response = jsonify({'error': 'Пользователь не является отправителем сообщения'})
        response.status_code = http.HTTPStatus.FORBIDDEN.value
        return response
    old_message.text = request.json.get('text')
    old_message.room_id = request.json.get('room_id')
    old_message.attachments = request.json.get('attachments')
    if not old_message:
        response = jsonify({'error': 'Сообщение не найдено'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    db.session.commit()
    return old_message.to_dict(), 201


@bp.route('/get-content/<path:name>', methods=['GET'])
@login_required
def get_content(name):
    """
    Возвращает медиа файл
    :param name: название медиа файла
    :return: медиа файл
    """
    response = send_from_directory(current_app.config['UPLOAD_FOLDER'], name)
    response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@socketio.on("connect")
@authenticated_only
def handle_connect():
    """
    Connect событие для сокета
    """
    users[current_user._get_current_object()] = request.sid
    emit('join', current_user.to_dict(), broadcast=True)


@socketio.on("join")
@authenticated_only
def on_join(data):
    """
    Событие входа, помещает пользователя в комнату
    :param data: JSON с идентификатором комнаты
    """
    if isinstance(data, str):
        data = json.loads(data)
    join_room(data['room_id'])


@socketio.on("leave")
@authenticated_only
def on_join(data):
    leave_room(data['room_id'])


@socketio.on("delete")
@authenticated_only
def on_join(data):
    """
    Событие вызываемое при удаление данных, например сообщения
    Отправляет событие "on_delete" клиенту
    :param data: JSON представления объекта
    """
    socketio.emit('on_delete', data)


@socketio.on("disconnect")
@authenticated_only
def handle_user_leave():
    """
    Событие отключения пользователя из сокет сессии
    Отправляет всем пользователям из сокет сессии сообщение
    "leave" с объектом пользователяt
    """
    leaved_user = None
    for user in users:
        if request.sid == users[user]:
            leaved_user = user
            break
    if leaved_user:
        socketio.start_background_task(update_last_seen, (current_app._get_current_object(), leaved_user.id,))
        emit('leave', leaved_user.to_dict(), broadcast=True)
        del users[leaved_user]


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
    if not msg['text']:
        return
    message = Message(user=current_user, text=msg['text'], date=datetime.datetime.utcnow(), room_id=msg['room_id'])
    db.session.add(message)
    db.session.commit()
    emit("chat", message.to_dict(), to=message.room_id)
    if not message.is_private():
        emit("notify", message.to_dict(), broadcast=True)


@socketio.on("private_message")
@authenticated_only
def handle_private_message(message):
    """
    Событие нового сообщения пользователю
    При вызове отправляет событие chat с объектом сообщения в формате JSON
    Отправляет событие notify всем пользователям в текущей сессии
    :param message: JSON представление с room_id, где room_id идентификатор комнаты
    """
    msg = message
    if not isinstance(message, dict):
        msg = json.loads(message)
    if not msg['text']:
        return
    user_id = msg['user_id']
    receiver = User.query.filter_by(id=user_id).first()
    if not receiver:
        return
    message = Message(user=current_user, text=msg['text'], date=datetime.datetime.utcnow(), receiver=user_id, user_id=current_user.id)
    emit("private", message.to_dict(), to=receiver)
    db.session.add(message)
    db.session.commit()

