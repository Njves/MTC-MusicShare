from datetime import datetime

from app import db


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(256), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    def to_dict(self):
        return {'type': self.type, 'link': self.link}

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    text = db.Column(db.String(), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, comment='last seen user in online')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'),
                        nullable=True)
    attachments = db.relationship('Attachment', backref='message', lazy=True)
    def to_dict(self):
        return {'username': self.username, 'text': self.text, 'date': str(self.date), 'attachments': [attachment.to_dict() for attachment in self.attachments]}


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    room_id = db.Column(db.String(), nullable=False)
    messages = db.relationship('Message', backref='room', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'room_id': self.room_id}
