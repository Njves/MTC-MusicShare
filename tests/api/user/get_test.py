from flask import jsonify

from tests.api import add_fixtures
from tests.data.user import user, john


def test_get_user_self(db_session, app):
    u = user()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        response = client.get(f'user/{u.id}')
        assert response.status_code == 200
        assert response.json == jsonify(u.to_dict()).json


def test_get_user(db_session, app):
    u = user()
    j = john()
    add_fixtures(db_session, u, j)
    with app.test_client(user=u) as client:
        response = client.get(f'user/{j.id}')
        assert response.status_code == 200
        assert response.json == jsonify(j.to_dict()).json


def test_get_user_not_found(db_session, app):
    u = user()
    add_fixtures(db_session, u)
    with app.test_client(user=u) as client:
        response = client.get('user/100000')
        assert response.status_code == 404
        assert response.json['error']

