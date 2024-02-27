from app import create_app, socketio

app = create_app()
if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, keyfile='key.pem', certfile='cert.pem')