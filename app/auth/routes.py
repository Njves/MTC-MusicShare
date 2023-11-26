import flask
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from app import db, login_manager
from app.auth import bp
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Auth page
    """
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('login')).first()
        print(user)
        if user is None:
            flash('Такого пользователя не существует')
            return redirect(url_for('auth.login'))
        print(str(request.form.get('password')))
        user.check_password(str(request.form.get('password')))
        if user.check_password(request.form.get('password')):
            login_user(user, remember=True)
            next = flask.request.args.get('next')
            flash('Вы авторизованы')
            return flask.redirect(next or url_for('chat.index'))
    redirect(url_for('auth.login'))
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        reg_login, reg_password = request.form.get('login'), request.form.get('password')
        if User.query.filter_by(username=reg_login).first() is None:
            user = User(username=reg_login)
            user.set_password(reg_password)
            db.session.add(user)
            db.session.commit()
        else:
            print('Такой пользователь уже суещствует')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
