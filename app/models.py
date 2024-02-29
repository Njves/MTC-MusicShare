from datetime import datetime, timedelta
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


subscribers = db.Table(
    'subscribers',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer(), db.ForeignKey('room.id'), ),
    db.UniqueConstraint('user_id', 'room_id')
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    email = db.Column(db.String(128), nullable=True)
    password_hash = db.Column(db.String(), nullable=False)
    color = db.Column(db.String(10), default='#000000')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, comment='last seen user in online')
    room_owner = db.relationship('Room', backref='owner', lazy=True)

    def __repr__(self) -> str:
        return f'(User {self.id}, Username: {self.username}, email: {self.email}, last_seen: {self.last_seen})'

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email, 'color': self.color,
                'last_seen': str(self.last_seen)}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __hash__(self):
        return hash((self.id, self.username, self.email, self.color, self.last_seen))

    def __eq__(self, other):
        if other is None:
            return False
        return (self.id, self.username, self.color,
                self.last_seen, self.email) == (other.id, other.username, other.color,
                                                other.last_seen, other.email)

    def get_user_token(self):
        return jwt.encode(
            {'user_id': self.id},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            account = User.query.get(jwt.decode(token, current_app.config['SECRET_KEY'],
                                                algorithms=['HS256'])['user_id'])
            return account
        except jwt.ExpiredSignatureError:
            return None  # Токен истек
        except jwt.InvalidTokenError:
            return None  # Недействительный токен


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(256), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), index=True)

    def to_dict(self):
        return {'type': self.type, 'link': self.link}

    @staticmethod
    def from_dict(attachment_dict):
        return Attachment(type=attachment_dict.get('type'), link=attachment_dict.get('link'),
                          message_id=attachment_dict.get('message_id'))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(256), nullable=True, index=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, comment='last seen user in online')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'),
                        nullable=True)
    attachments = db.relationship('Attachment', backref='message', lazy=True, cascade='all,delete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=True)
    user = db.relationship('User', backref='messages', lazy=True, foreign_keys=[user_id])
    receiver = db.Column(db.Integer, db.ForeignKey('user.id'),
                         nullable=True)
    received_messages = db.relationship('User', backref='received_messages', lazy=True, foreign_keys=[receiver])

    def is_private(self):
        return self.receiver is not None

    def to_dict(self):
        return {'id': self.id, 'text': self.text, 'receiver': self.receiver, 'date': str(self.date),
                'attachments': [attachment.to_dict() for attachment in self.attachments],
                'user': self.user.to_dict(), 'room_id': self.room_id}

    @staticmethod
    def from_dict(message_dict):
        return Message(text=message_dict.get('text'), room_id=message_dict.get('room_id'),
                       user_id=message_dict.get('user_id'), receiver=message_dict.get('receiver_id'))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(18), nullable=False, unique=True, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                         nullable=True)
    messages = db.relationship('Message', backref='room', lazy='dynamic', order_by="Message.date.desc()")
    subscribers = db.relationship('User', secondary=subscribers)

    def __repr__(self):
        return self.name

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'owner_id': self.owner_id}

    @staticmethod
    def is_exists(room_id):
        return Room.query.filter_by(id=room_id).first()


class FCMTokens(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                         unique=True)
    token = db.Column(db.String, nullable=False)
