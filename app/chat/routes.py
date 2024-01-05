import datetime
import json
import os

import faker
import flask
from flask import request, render_template, redirect, jsonify, url_for, current_app, send_from_directory
from flask_socketio import emit
from werkzeug.utils import secure_filename

from app import socketio, db
from app.chat import bp
from app.models import Message, Room, Attachment

users = {}
fake = faker.Faker()


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
    return render_template('chat/enter.html')


@bp.route('/search-message')
def search_messages():
    username = request.args.get('username')
    query = request.args.get('query')
    result = Message.query.filter(Message.text.like("%" + query + "%")).all()
    result = [message.to_dict() for message in result]
    return jsonify({'result': result})

@bp.route('/get-current-room')
def get_current_room():
    username = request.args.get('username')
    if not username:
        return flask.abort(400)
    if username not in users.keys():
        return flask.abort(404)
    room_id = flask.session.get('current_room')
    room = Room.query.filter_by(id=room_id).first()
    if not room:
        return flask.abort(404)
    return jsonify(room.to_dict())


@bp.route("/get-username", methods=['GET', 'POST'])
def get_username():
    """
    Return username from current server session
    :return:
    """
    if not flask.session.get('username'):
        return flask.abort(404)
    return jsonify({'username': flask.session['username'], 'room': Room.query.filter_by(id=flask.session.get('current_room')).first().to_dict()})


@bp.route("/get-rooms")
def get_rooms():
    """
    Return current available rooms
    :return: json with list of rooms
    """
    return jsonify({'rooms': [room.to_dict() for room in Room.query.all()]})


@bp.route("/create-room", methods=['POST'])
def create_room():
    """
    Create new room and return it object
    :return: new room object json
    """
    username = request.json.get('username')
    if not username:
        return flask.abort(403)
    rooms_names = ['Python', 'Java', 'C#', 'C', 'C++', 'Andrey']
    new_rooms = []
    for room_name in rooms_names:
        print(Room.query.filter_by(name=room_name).first())
        if Room.query.filter_by(name=room_name).first():
            continue
        new_rooms.append(Room(name=room_name))
        db.session.add(new_rooms[-1])
        new_rooms[-1] = new_rooms[-1].to_dict()
    db.session.commit()
    return jsonify({'rooms': new_rooms})


@bp.route("/create-room/<room_name>", methods=['POST'])
def create_room_with_name():
    """
    Create new room and return it object
    :return: new room object json
    """
    username = request.json.get('username')
    room_name = request.json.get('room_name')
    if not username:
        return flask.abort(403)
    room = Room(name=room_name)
    db.session.add()
    db.session.commit()
    return jsonify({'room': room})


@bp.route("/join-room/<int:id>")
def join_room(room_id):
    """
    Connect User to room
    :param room_id: id from database
    :return:
    """
    return jsonify({'rooms': rooms})


@bp.route("/get-notify-message", methods=['GET'])
def get_notify():
    """
    Return notify sound
    :return: .mp3 file
    """
    return send_from_directory('static/sound', 'msg_notify.mp3')


@bp.route('/check-username', methods=['GET'])
def check_busy_username():
    """
    Check busy usernames in current session
    :return:
    """
    print(request.args['username'], users.keys(), )
    if request.args['username'] in users.keys():
        return {}, 409
    return {}, 200


@bp.route("/chat", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not request.form['username']:
            return redirect(url_for('chat.index'), code=400)
        if len(request.form['username']) >= 30:
            return redirect(url_for('chat.index'), code=413)
        flask.session['username'] = request.form['username']
        flask.session.permanent = True
        return redirect(url_for('chat.index'))
    if not flask.session.get('username'):
        return redirect(url_for('chat.enter'), code=403)
    return render_template('chat/index.html')


@bp.route("/get-history", methods=['GET'])
def get_history():
    messages = Message.query.all()
    messages = [msg.to_dict() for msg in messages]
    return jsonify({'messages': messages})


@bp.route("/get-history/<room_name>", methods=['GET'])
def get_history_by_room_name(room_name=None):
    room = Room.query.filter_by(name=room_name).first()
    if not room:
        return flask.abort(404)
    flask.session['current_room'] = room.id
    return jsonify({'messages': [message.to_dict() for message in room.messages]})


@bp.route("/get-online", methods=['GET'])
def get_users_online():
    for i in range(10):
        users[fake.name()] = 1
    return jsonify(list(users.keys()))


@bp.route("/attach", methods=['POST'])
def attach():
    if 'attach_file' not in request.files:
        return {}, 400
    file = request.files['attach_file']
    if file.filename == '':
        return {}, 400
    filename = f'{secure_filename(file.filename)}_{datetime.datetime.utcnow().date()}_{str(datetime.datetime.utcnow().time()).replace(":", ".")}'
    username = request.form['username']
    text = request.form['text']
    link = os.path.join(os.path.join('app', current_app.config['UPLOAD_FOLDER']), filename)
    file.save(link)
    link = url_for('chat.get_content', name=filename)
    message = Message(username=username, text=text, date=datetime.datetime.utcnow())
    attachment = Attachment(type=file.content_type, link=link)
    message.attachments.append(attachment)
    db.session.add(attachment)
    db.session.add(message)
    db.session.commit()
    socketio.emit('chat', message.to_dict())
    return message.to_dict()


@bp.route('/get-content/<path:name>', methods=['GET'])
def get_content(name):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], name)


@socketio.on("connect")
def handle_connect():
    username = flask.session.get('username')
    users[username] = request.sid
    emit('join', {'username': username, 'date': str(datetime.datetime.utcnow()), 'room': Room.query.filter_by(id=flask.session.get('current_room')).first().to_dict()}, broadcast=True)


@socketio.on("disconnect")
def handle_user_leave():
    leaved_user = None
    for username in users:
        if request.sid == users[username]:
            leaved_user = username
            del users[username]
            break
    emit('leave', {'username': leaved_user}, broadcast=True)


def add_message(app, message):
    with app.app_context():
        db.session.add(message)
        db.session.commit()


@socketio.on("new_message")
def handle_new_message(message):
    msg = json.loads(message)
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user
    message = Message(username=username, text=msg['text'], date=datetime.datetime.utcnow())
    emit("chat", message.to_dict(), broadcast=True)
    socketio.start_background_task(add_message, current_app._get_current_object(), message)
