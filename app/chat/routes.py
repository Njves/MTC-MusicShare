import json

import flask
from flask import request, render_template, redirect, jsonify, url_for
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


@bp.route("/chat", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        flask.session['username'] = request.form['username']
        flask.session.permanent = True
        return redirect(url_for('chat.index'))
    if not flask.session.get('username'):
        return redirect('chat.enter')
    return render_template('chat/index.html')

@bp.route("/get-history", methods=['GET'])
def get_history():
    messages = Message.query.all()
    messages = [msg.to_dict() for msg in messages]

    return jsonify({'messages':messages})

@socketio.on("connect")
def handle_connect():
    print("Client connected!")


@socketio.on("user_join")
def handle_user_join(msg):
    message = json.loads(msg)
    username = message['username']
    users[username] = request.sid
    emit("chat", {"message": f'Челик {username} зашел в чят', "username": username}, broadcast=True)


@socketio.on("new_message")
def handle_new_message(message):
    msg = json.loads(message)
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user
    message = Message(username=username, text=msg['message'])
    db.session.add(message)
    db.session.commit()
    emit("chat", {"message": msg['message'], "username": username}, broadcast=True)
