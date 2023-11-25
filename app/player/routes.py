from flask import request, render_template, url_for
from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from app.player import bp
import json

users = {}


@bp.route("/player")
def index():
    return render_template('player/index.html')


def read_in_chunks(file_path, chunk_size=4096):
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk


@socketio.on("connect", namespace='/stream')
def handle_connect():
    print("Client connected!")
    filepath = 'app/static/music/Синдром Восьмиклассника - Снафф-порно.wav'
    print(filepath)
    for chunk in read_in_chunks(filepath):
        print(chunk)
        emit('message', {'chunk': chunk}, namespace='/stream')
