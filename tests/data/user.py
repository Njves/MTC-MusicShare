from app.models import User, Room, Message, Attachment
from datetime import datetime
import faker

fake = faker.Faker()

def user():
    u1 = User(username='user', last_seen=datetime.utcnow(), color='#000', email='email@gmail.com')
    u1.set_password('123456')
    return u1


def john():
    j = User(username='John Doe', last_seen=datetime.utcnow(), color='#000', email='johndoe@gmail.com')
    j.set_password('123456')
    return j


def attachments():
    return [Attachment(type='img', link='link.png')]


def messages():
    msg_with_attachment = Message(text="Test")
    msg_with_attachment.attachments = attachments()
    return [Message(text='Text'), msg_with_attachment]

def room(user):
    return rooms([user]).pop(0)

def rooms(users):
    test_rooms = []
    for u in users:
        room = Room(name=fake.name(), owner_id=u.id)
        room.messages = messages()
        test_rooms.append(room)
    return test_rooms

def color_not_valid():
    return ['#', '#0', '#00', '#FF', 'J', "#J", "#jjj", '#\\\\', '#//', '#---']


def color_valid():
    return ['#000', '#F00', '#000FFF']


def passwords():
    return ['0', '00', '000', '0000', '00000']
