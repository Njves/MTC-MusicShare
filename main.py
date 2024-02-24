from app import create_app, socketio

app = create_app()
if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    socketio.run(app, host='10.3.226.173', debug=True, allow_unsafe_werkzeug=True)