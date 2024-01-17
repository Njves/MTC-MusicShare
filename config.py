import os
import pathlib


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    # postgresql://njves:ViX8tAxl4Gn67J8kplD9uA8gAC451IM2@dpg-clpv7phjvg7s73e1e8m0-a.frankfurt-postgres.render.com/kursoagregator
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB')
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'some-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MUSIC_DIR = pathlib.Path('app/static/music')
    CACHE_TYPE = 'SimpleCache'  # Flask-Caching related configs
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_DEFAULT_TIMEOUT = 300
    UPLOAD_FOLDER = 'content'
    MESSAGE_PART = 10
    MAX_CONTENT_LENGTH = 16 * 10 ** 6
