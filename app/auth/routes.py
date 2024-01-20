from http import HTTPStatus

import flask
from flask import render_template, request, redirect, url_for, abort, Response
from flask_login import login_user, logout_user, login_required, current_user

from app import db, login_manager
from app.auth import bp
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
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
            next_arg = flask.request.args.get('next')
            return redirect(next_arg or url_for('site.index'))
        response = flask.make_response({'error': 'Пароль неверный'}, 401)
        return response
    return render_template('chat/enter.html')


@bp.route("/register", methods=['GET', 'POST'])
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
        if not user.set_password(reg_password):
            response = flask.make_response({'error': 'Слишком короткий пароль'}, 409)
            return response
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        next_arg = flask.request.args.get('next')
        return redirect(next_arg or url_for('site.index'))
    return render_template('chat/register.html')


@login_manager.unauthorized_handler
def unauthorized() -> Response:
    if request.blueprint == 'chat':
        abort(HTTPStatus.UNAUTHORIZED)
    return redirect(login_manager.login_view)


@bp.route("/logout", methods=['GET'])
@login_required
def logout() -> Response:
    logout_user()
    response = redirect(url_for('auth.login'))
    response.delete_cookie('current_room')
    return response
