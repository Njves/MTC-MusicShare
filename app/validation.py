import re
from app.models import User


def color_valid(color: str) -> bool:
    return bool(re.compile('^#(?:[0-9a-fA-F]{3}){1,2}$').match(color))


def length_password_valid(password: str) -> bool:
    return False


def user_same_name_valid(app, username: str) -> bool:
    with app.app_context():
        return bool(User.query.filter_by(username=username).first())


def user_exists_by_id(app, id):
    with app.app_context():
        return bool(User.query.get(id))


def length_field(string, min_length=0, max_length=128):
    return min_length <= len(string) <= max_length
