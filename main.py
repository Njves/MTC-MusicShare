from app import create_app, socketio

app = create_app()
if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    socketio.run(host='0.0.0.0',debug=True)