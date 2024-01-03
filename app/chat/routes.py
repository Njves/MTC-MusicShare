import json
import datetime
import os
import flask
import faker
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename
from flask import request, render_template, redirect, jsonify, url_for, current_app, send_from_directory
from flask_socketio import emit
from app import socketio, db
from app.chat import bp
from app.models import Message, Room, Attachment
from config import basedir

users = {}
fake = faker.Faker()


@bp.route("/", methods=['GET', 'POST'])
def enter():
    return render_template('chat/enter.html')


@bp.route("/get-username", methods=['GET', 'POST'])
def get_username():
    return jsonify({'username': flask.session['username']})


@bp.route("/get-rooms")
def get_rooms():
    fake = faker.Faker()
    rooms = [Room(name=fake.name(), id=fake.address()).to_dict() for i in range(10)]
    return jsonify({'rooms': rooms})


@bp.route("/create-room", methods=['POST'])
def create_room():
    fake = faker.Faker()
    rooms = [Room(name=fake.name(), id=fake.address()).to_dict() for i in range(10)]
    return jsonify({'rooms': rooms})


@bp.route("/join-room/<int:id>")
def join_room(room_id):
    return jsonify({'rooms': rooms})


@bp.route("/get-notify-message", methods=['GET'])
def get_notify():
    return url_for('static', filename='sound/msg_notify.mp3')


@bp.route('/check-username', methods=['GET'])
def check_busy_username():
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
    emit('join', {'username': username, 'date': str(datetime.datetime.utcnow())}, broadcast=True)


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
