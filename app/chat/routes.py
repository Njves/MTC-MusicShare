from datetime import datetime

from flask import request, render_template, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.chat import bp
import json

from app.models import User, Message

users = {}


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route("/chat", methods=['GET', 'POST'])
@login_required
def index():
    messages = Message.query.all()
    return render_template('chat/index.html', history=messages)

@socketio.on("connect")
def handle_connect():
    print("Client connected!")


@socketio.on("user_join")
def handle_user_join(msg):
    message = json.loads(msg)
    username = message['username']
    users[username] = request.sid
    emit("chat", {"message": f'Челик {username} зашел в чят', "username": username})


@socketio.on("new_message")
def handle_new_message(message):
    print(f"New message: {message}")
    msg = json.loads(message)
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user
    message = Message(sender_id=User.query.filter_by(username=username).first().id, text=msg['message'])
    db.session.add(message)
    db.session.commit()
    emit("chat", {"message": msg['message'], "username": username}, broadcast=True)
