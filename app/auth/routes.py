import flask
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import iri_to_uri

from app import db, login_manager
from app.auth import bp
from app.models import User



@bp.route('/login', methods=['GET', 'POST'])
def login():
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
            next = flask.request.args.get('next')
            return redirect(next or url_for('chat.index'))
        response = flask.make_response({'error': 'Пароль неверный'}, 401)
        return response
    return render_template('chat/enter.html')


@bp.route("/register", methods=['GET', 'POST'])
def register():
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
        login_user(user, remember=True)
        db.session.add(user)
        db.session.commit()
        next = flask.request.args.get('next') if flask.request.args.get('next') else url_for('chat.index')
        response = flask.make_response({'access_token': user.get_user_token()}, 303)
        location = iri_to_uri(next, safe_conversion=True)
        response.headers['Location'] = location
        return response
    return render_template('chat/enter.html')


@bp.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
