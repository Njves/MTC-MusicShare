import flask
from flask import redirect, render_template, request
from flask_login import login_required, current_user

from app import db
from app.models import Room
from app.room import bp


@bp.route('', methods=['POST'])
def create(user_id):
    if request.method == 'POST':
        title, description, password, songs = request.form.get('title_room'), request.form.get(
            'description_room'), request.form.get('password_room'), request.form.get('songs_room')
        room = Room(creator_id=user_id, title=title, songs=songs,
                    description=description, password=password)
        db.session.add(room)
        db.session.commit()
        # комната успешно создано, обнови страницу
        return render_template()


@bp.route('', methods=['POST'])
def delete():
    if request.method == 'POST':
        id = request.form.get('id')
        Room.query.filter_by(id=id).delete()
        db.session.commit()
        # комната успешно удалена, обнови страницу
        return redirect()


@bp.route('/enter_room/<int:room_id>', methods=['POST'])
@login_required
def enter_room(room_id):
    room = Room.query.get(room_id)
    if room:
        if current_user in room.users:
            # Юзер уже зашел туда с другой вкладки, просто закинь его
            return redirect()
        password = request.form.get('password')
        if room.password and room.password != password:
            # Не вошел, ошибка пароля
            return redirect()
        room.users.append(current_user)
        db.session.commit()
        # Вошел по паролю
        return redirect()
    else:
        # комната уже удалена или недоступна по иным причинам, просто обновить
        return redirect()


@bp.route('', methods=['POST'])
@login_required
def logout_from_room(room_id):
    room = Room.query.get(room_id)
    if room:
        room.users.remove(current_user)
        db.session.commit()
        # пользователь вышел, перенаправить из комнаты куда-нибудь
        return redirect()
