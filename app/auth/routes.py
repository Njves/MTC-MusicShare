from http import HTTPStatus

import flask
from flask import render_template, request, redirect, url_for, current_app, Response
from flask_login import login_user, logout_user, login_required, current_user

from app import db, login_manager, validation
from app.auth import bp
from app.models import User

@bp.after_request
def after(response):
    current_app.logger.debug(response.headers)
    current_app.logger.debug(response.get_data())
    return response

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.args.get('api_key')
    if api_key:
        user = User.verify_token(api_key)
        if user:
            return user
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Bearer ', '', 1)
        current_app.logger.debug(api_key)
        user = User.verify_token(api_key)
        current_app.logger.debug(user)
        if user:
            return user
    return None

@bp.route('/login', methods=['POST'])
def login() -> str | Response:
    """
    Auth page
    """
    if request.method == 'POST':
        user_json = request.json
        user = User.query.filter_by(username=user_json.get('username')).first()
        if user is None:
            response = flask.make_response({'error': 'Пользователя не существует'}, 404)
            return response
        user.check_password(str(user_json.get('password')))
        if user.check_password(user_json.get('password')):
            if color := user_json.get('color'):
                user.color = color
                db.session.add(user)
                db.session.commit()
            login_user(user, remember=True)

            return {'token': user.get_user_token(), 'user': user.to_dict()}, 200
        response = flask.make_response({'error': 'Пароль неверный'}, 401)
        return response
    return render_template('chat/enter.html')


@bp.route("/register", methods=['POST'])
def register() -> str | Response:
    if current_user.is_authenticated:
        return flask.make_response({'message': 'Вы уже вошли в систему'}, 403)
    if request.method == 'POST':
        registration_json = request.json
        reg_login, reg_password = registration_json.get('username'), registration_json.get('password')
        if len(reg_login) > 128 or len(reg_password) > 128:
            response = flask.make_response({'error': 'Слишком длинные значения'}, 400)
            return response
        if User.query.filter_by(username=reg_login).first():
            response = flask.make_response({'error': 'Такой пользователь уже существует'}, 409)
            return response
        user = User(username=reg_login)
        user.set_password(reg_password)
        if not validation.length_password_valid(reg_password):
            response = flask.make_response({'error': 'Слишком короткий пароль'}, 409)
            return response
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return {'token': user.get_user_token(), 'user': user.to_dict()}, 201
    return render_template('chat/register.html')



@bp.route("/logout", methods=['GET'])
@login_required
def logout() -> Response:
    logout_user()
    response = redirect(url_for('auth.login'))
    response.delete_cookie('current_room')
    return response

@bp.route('/user', methods=['GET'])
def get_token():
    token = request.args.get('token')
    current_app.logger.debug('token', token)
    try:
        user = User.verify_token(token)
        current_app.logger.debug('token', user)
        if not user:
            return {}, 404
    except e:
        return {'error': e}, 401
    return user.to_dict()

@bp.route('/refresh', methods=['GET'])
def get_refresh():
    token = flask.session.get('refresh')
    if not token:
        return {'error': 'Token is expired'}, 404
    return token
