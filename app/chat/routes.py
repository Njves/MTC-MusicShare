from flask import request, render_template
from flask_socketio import emit
from app import socketio
from app.chat import bp

users = {}

@bp.route("/chat"
          "")
def index():
    return render_template('chat/index.html/')
@socketio.on("connect")
def handle_connect():
    print("Client connected!")

@socketio.on("user_join")
def handle_user_join(username):
    print(f"User {username} joined!")
    users[username] = request.sid

@socketio.on("new_message")
def handle_new_message(message):
    print(f"New message: {message}")
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user
    emit("chat", {"message": message, "username": username}, broadcast=True)