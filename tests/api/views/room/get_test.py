from tests.api import add_fixtures
from tests.data.user import user, rooms


def test_get_rooms(db_session, client):
    room = rooms([user()])
    add_fixtures(db_session, *room)
    response = client.get('get-rooms')
    assert response.status_code == 200
    assert response.json == [r.to_dict() for r in room]


def test_get_room(db_session, client):
    rooms_data = rooms([user()])
    add_fixtures(db_session, *rooms_data)
    response = client.get('get-rooms')
    assert response.status_code == 200
    assert response.json == [room.to_dict() for room in rooms_data]

