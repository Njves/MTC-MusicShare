from app.models import User
from datetime import datetime


def user():
    u1 = User(username='user', last_seen=datetime.utcnow(), color='#000', email='email@gmail.com')
    u1.set_password('123456')
    return u1

def john():
    j = User(username='John Doe', last_seen=datetime.utcnow(), color='#000', email='johndoe@gmail.com')
    j.set_password('123456')
    return j

def color_not_valid():
    return ['#', '#0', '#00', '#FF', 'J', "#J", "#jjj", '#\\\\', '#//', '#---']

def color_valid():
    return ['#000', '#FF0', '#FFF000']

def passwords():
    return ['0', '00', '000', '0000', '00000']
