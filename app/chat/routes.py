from flask import request, render_template
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.chat import bp
import json

users = {}

@bp.route("/chat")
def index():
    return render_template('chat/index.html/')
@socketio.on("connect")
def handle_connect():
    print("Client connected!")

@socketio.on("user_join")
def handle_user_join(msg):
    print(msg)
    message = json.loads(msg)
    username = message['username']
    room = message['room']
    join_room(room)
    print(f"User {username} to {room} joined!")
    users[username] = request.sid
    emit("chat", {"message": 'Челик зашел в чят', "username": username}, to=room)
@socketio.on("new_message")
def handle_new_message(message):
    print(f"New message: {message}")
    msg = json.loads(message)
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user
    emit("chat", {"message": msg['message'], "username": username}, to=msg['room'])