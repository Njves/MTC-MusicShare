from tests.api import add_fixtures
from tests.data.user import user, john, color_not_valid, color_valid, passwords
import json


def test_user_edit(db_session, app):
    u = user()
    j = john()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        response = client.put(f'user/{u.id}', json=j.to_dict())
        assert response.status_code == 201
        edited_user = response.json
        j_dict = j.to_dict()
        # Удаляем так как эти параметры неизменяемые или изменяются
        # Слишком часто
        del edited_user['last_seen']
        del edited_user['id']
        del j_dict['last_seen']
        del j_dict['id']
        assert edited_user == j_dict


def test_user_edit_not_valid_color(db_session, app):
    u = user()
    j = john()
    not_valid_colors = color_not_valid()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        j_dict = j.to_dict()
        for color in not_valid_colors:
            j_dict['color'] = color
            response = client.put(f'user/{u.id}', json=j_dict)
            assert response.status_code == 409
            assert response.json

def test_user_edit_valid_color(db_session, app):
    u = user()
    j = john()
    not_valid_colors = color_not_valid()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        j_dict = j.to_dict()
        for color in color_valid():
            j_dict['color'] = color
            response = client.put(f'user/{u.id}', json=j_dict)
            assert response.status_code == 201
            assert response.json


def test_user_already_exists(db_session, app):
    u = user()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        response = client.put(f'user/{u.id}', json=u.to_dict())
        assert response.status_code == 409
        assert response.json

def test_user_password_to_short(db_session, app):
    u = user()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        u_dict = u.to_dict()
        for index, password in enumerate(passwords()):
            u_dict['password'] = password
            response = client.put(f'user/{u.id}', json=u.to_dict())
            assert response.status_code == 409
            assert response.json
