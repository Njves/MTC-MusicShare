import json
import datetime
import flask
from flask import request, render_template, redirect, jsonify, url_for, current_app
from flask_socketio import emit
from app import socketio, db
from app.chat import bp
from app.models import Message

users = {}


@bp.route("/", methods=['GET', 'POST'])
def enter():
    messages = Message.query.all()
    return render_template('chat/enter.html', history=messages)


@bp.route("/get-username", methods=['GET', 'POST'])
def get_username():
    return jsonify({'username': flask.session['username']})

@bp.route("/get-rooms")
def get_rooms():


@bp.route("/get-notify-message", methods=['GET'])
def get_notify():
    return url_for('static', filename='sound/msg_notify.mp3')


@bp.route("/chat", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not request.form['username']:
            return redirect(url_for('chat.index'))
        if len(request.form['username']) >= 30:
            return redirect(url_for('chat.index'))
        flask.session['username'] = request.form['username']
        flask.session.permanent = True
        return redirect(url_for('chat.index'))
    if not flask.session.get('username'):
        return redirect(url_for('chat.enter'))
    return render_template('chat/index.html')


@bp.route("/get-history", methods=['GET'])
def get_history():
    messages = Message.query.all()
    messages = [msg.to_dict() for msg in messages]
    return jsonify({'messages': messages})


@bp.route("/get-online", methods=['GET'])
def get_users_online():
    return jsonify(list(users.keys()))


@socketio.on("connect")
def handle_connect():
    username = flask.session.get('username')
    users[username] = request.sid
    emit("chat",
         {"text": f'Челик {username} зашел в чят', "username": username, 'date': str(datetime.datetime.utcnow())},
         broadcast=True)
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
    emit("chat", {"text": msg['text'], "username": username, "date": str(message.date)}, broadcast=True)
    socketio.start_background_task(add_message, current_app, message)