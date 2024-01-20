from tests.api import add_fixtures
from tests.data.user import user, john, color_not_valid, color_valid, passwords


def test_user_edit(db_session, client):
    u = user()
    j = john()
    add_fixtures(db_session, u)
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


def test_user_edit_not_valid_color(db_session, client):
    u = user()
    j = john()
    color = color_not_valid()[0]
    add_fixtures(db_session, u)
    j_dict = j.to_dict()
    j_dict['color'] = color
    response = client.put(f'user/{u.id}', json=j_dict)
    assert response.status_code == 409
    assert response.json.get('error') == 'Invalid color'


def test_user_edit_valid_color(db_session, client):
    u = user()
    j = john()
    color = color_valid()[0]
    add_fixtures(db_session, u)
    j_dict = j.to_dict()
    j_dict['color'] = color
    response = client.put(f'user/{u.id}', json=j_dict)
    assert response.status_code == 201


def test_user_already_exists(db_session, client):
    u = user()
    add_fixtures(db_session, u)
    response = client.put(f'user/{u.id}', json=u.to_dict())
    assert response.status_code == 422
    assert response.json.get('error') == 'The name is occupied'


def test_user_password_to_short(db_session, client):
    u = user()
    add_fixtures(db_session, u)
    u_dict = u.to_dict()
    del u_dict['username']
    u_dict['password'] = '123'
    response = client.put(f'user/{u.id}', json=u_dict)
    assert response.status_code == 409
    assert response.json.get('error') == 'The password must be more than 6 characters long'

def test_user_exists_by_id(db_session, client):
    u = user()
    add_fixtures(db_session, u)
    response = client.put(f'user/1000', json=u.to_dict())
    assert response.status_code == 404



