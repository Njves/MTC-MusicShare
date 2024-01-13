import datetime
import http
import json
import os
import uuid

import flask
from flask import request, render_template, redirect, jsonify, url_for, current_app, send_from_directory
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from werkzeug.utils import secure_filename

from app import socketio, db, login_manager
from app.chat import bp
from app.image_converter import compress_image
from app.models import Message, Room, Attachment, User

# from app.cache import cache_html, cache_rooms
users = {}

# @login_manager.request_loader
# def load_user_from_request(request):
#     if request.headers.get('grant'):
#         return User.query.all()[0]
#     if api_key := request.args.get('access_token'):
#         user = User.verify_token(api_key)
#         return user
#     api_key = request.headers.get('Authorization')
#     print('api key', api_key)
#     if api_key:
#         api_key = api_key.replace('Bearer ', '', 1)
#         user = User.verify_token(api_key)
#         if user:
#             return user
#     return None


@bp.before_request
def init():
    if not Room.query.filter_by(name='Общая комната').first():
        room = Room(name='Общая комната')
        db.session.add(room)
        db.session.commit()
        flask.session['current_room'] = room.id
    if not flask.session.get('current_room'):
        room_id = Room.query.filter_by(name='Общая комната').first().id
        flask.session['current_room'] = room_id
        flask.session.permanent = True


@bp.route("/", methods=['GET'])
def enter():
    """
    Main enter page
    :return:
    """
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('chat.index'))


@bp.route('/search-message')
def search_messages():
    username = request.args.get('username')
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
    return jsonify(current_user.to_dict())


@bp.route("/get-rooms")
@login_required
def get_rooms():
    """
    Return current available rooms
    :return: json with list of rooms
    """
    rooms = [room.to_dict() for room in Room.query.all()]
    response = jsonify({'rooms': rooms})
    # response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route("/create-room", methods=['POST'])
@login_required
def create_room():
    """
    Create new room and return it object
    :return: new room object json
    """
    room_name = request.json.get('room_name')
    new_room = Room(name=room_name)
    db.session.add(new_room)
    db.session.commit()
    socketio.emit('new_room', {'room': new_room.to_dict()})
    return jsonify({'room': new_room.to_dict()})


@bp.route("/get-notify-message", methods=['GET'])
def get_notify():
    """
    Return notify sound
    :return: .mp3 file
    """
    return send_from_directory('static/sound', 'msg_notify.mp3')


@bp.route("/chat", methods=['GET', 'POST'])
def index():
    return render_template('chat/index.html')


@bp.route("/get-room/<int:room_id>", methods=['GET'])
@login_required
def get_history_by_room_name(room_id):
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        response = jsonify({'error': 'Комната не найдена'})
        response.status_code = http.HTTPStatus.NOT_FOUND.value
        return response
    room_dict = room.to_dict()
    room_dict['messages'] = [message.to_dict() for message in room.messages]
    response = jsonify(room_dict)
    response.delete_cookie('current_room')
    response.set_cookie('current_room', f'{room.id}', 60 * 60 * 24 * 30)
    # response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@bp.route("/get-online", methods=['GET'])
@login_required
def get_users_online():
    # online = User.query.filter(User.id.in_(list(users.keys()))).all()
    return jsonify([user.to_dict() for user in users.keys()])


@bp.route("/img-attach", methods=['POST'])
@login_required
def attach():
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
    compress_image(link)
    link = url_for('chat.get_content', name=filename)
    message = Message(user_id=current_user.id, text=text, date=datetime.datetime.utcnow(), room_id=room_id)
    attachment = Attachment(type=file.content_type, link=link)
    message.attachments.append(attachment)
    db.session.add(attachment)
    db.session.add(message)
    db.session.commit()
    socketio.emit('chat', message.to_dict())
    return message.to_dict()


@bp.route("/music-attach", methods=['POST'])
@login_required
def music_attach():
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
    filename = f'{filename}_${uuid.uuid4()}.{ext}'
    text = request.form.get('text')
    room_id = request.form.get('room_id')
    if not text:
        text = ''
    link = os.path.join(os.path.join('app', current_app.config['UPLOAD_FOLDER']), filename)
    file.save(link)
    link = url_for('chat.get_content', name=filename)
    message = Message(user_id=current_user.id, text=text, date=datetime.datetime.utcnow(), room_id=room_id)
    attachment = Attachment(type=file.content_type, link=link)
    message.attachments.append(attachment)
    db.session.add(attachment)
    db.session.add(message)
    db.session.commit()
    socketio.emit('chat', message.to_dict())
    return message.to_dict()


@bp.route('/message/<int:msg_id>', methods=['DELETE'])
@login_required
def remove_message(msg_id):
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
    response = send_from_directory(current_app.config['UPLOAD_FOLDER'], name)
    response.headers['Cache-Control'] = 'public,max-age=300'
    return response


@socketio.on("connect")
def handle_connect():
    users[current_user._get_current_object()] = request.sid
    emit('join', current_user.to_dict(), broadcast=True)


@socketio.on("join")
def on_join(data):
    join_room(data['room_id'])


@socketio.on("leave")
def on_join(data):
    leave_room(data['room_id'])


@socketio.on("delete")
def on_join(data):
    socketio.emit('on_delete', data)


@socketio.on("disconnect")
def handle_user_leave():
    leaved_user = None
    for user in users:
        if request.sid == users[user]:
            leaved_user = user
            break
    if leaved_user:
        emit('leave', User.query.get(leaved_user).to_dict(), broadcast=True)
        del users[leaved_user]


@socketio.on("new_message")
def handle_new_message(message):
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
