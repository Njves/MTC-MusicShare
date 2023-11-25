import os
import pathlib
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'some-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MUSIC_DIR = pathlib.Path('app/static/music')
