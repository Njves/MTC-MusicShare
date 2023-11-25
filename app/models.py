from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

users_room = db.Table('users_room',
                      db.Column('user_id', db.Integer, db.ForeignKey(
                          'user.id', ondelete='CASCADE')),
                      db.Column('room_id', db.Integer, db.ForeignKey('room.id', ondelete='CASCADE')))

playlist_songs = db.Table('playlist_songs',
                          db.Column('playlist_id', db.Integer, db.ForeignKey(
                              'playlist.id', ondelete='CASCADE')),
                          db.Column('song_id', db.Integer, db.ForeignKey('song.id', ondelete='CASCADE')))

user_songs = db.Table("user_songs",
                      db.Column('user_id', db.Integer, db.ForeignKey(
                          'user.id', ondelete='CASCADE')),
                      db.Column('song_id', db.Integer, db.ForeignKey('song.id', ondelete='CASCADE')))

user_playlists = db.Table("user_playlists",
                          db.Column('user_id', db.Integer, db.ForeignKey(
                              'user.id', ondelete='CASCADE')),
                          db.Column('playlist_id', db.Integer, db.ForeignKey('song.id', ondelete='CASCADE')))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, default="")
    password_hash = db.Column(db.String(256), nullable=False)
    songs = db.relationship('User_songs', secondary=user_songs, lazy='dynamic')
    playlists = db.relationship('User_playlists', secondary=user_playlists, lazy='dynamic')

    def __repr__(self) -> str:
        return f'User {self.id}, Username: {self.username}, email: {self.email}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'))
    description = db.Column(db.String(), nullable=False)
    users = db.relationship('Users', backref='room', secondary=users_room,
                            lazy='dynamic')

    def __repr__(self) -> str:
        return f'Room {self.id}, description: {self.description}'


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    songs = db.relationship('Songs', secondary=playlist_songs,
                            lazy='dynamic')

    def __repr__(self):
        return f'Playlist: {self.id}, title: {self.title}, description: {self.description}'


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    artist = db.Column(db.String(128), nullable=False, default="")
    file_url = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'Song: {self.id}, title: {self.title}, artist: {self.artist},' \
               f'file_url: {self.file_url}'
