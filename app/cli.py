import os
import shutil

from flask import current_app

from app import db
from app.models import Room


@current_app.cli.command('clear-content')
def clear():
    """ Удаляет все картинки """
    if os.path.exists(f'./app/{current_app.config["UPLOAD_FOLDER"]}'):
        shutil.rmtree(f'./app/{current_app.config["UPLOAD_FOLDER"]}')
        os.mkdir('./app/content/')

@current_app.cli.command('init')
def init():
    if not Room.query.filter_by(name='Общая комната').first():
        room = Room(name='Общая комната')
        db.session.add(room)
        db.session.commit()
        print('Success')