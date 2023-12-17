from datetime import datetime

from app import db


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    text = db.Column(db.String(), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, comment='last seen user in online')
    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'text': self.text, 'date': self.date}

