from tests.api import add_fixtures
from tests.data.user import rooms, user, room


def test_create_room(db_session, client):
    u = user()
    add_fixtures(db_session, u)
    test_room = room(u)
    response = client.post('create-room', json=test_room.to_dict())
    assert response.status_code == 201
    assert response.json == {'id': 1, 'name': test_room.name, 'owner_id': u.id, 'owner': u.to_dict(), 'messages': [message.to_dict() for message in test_room.messages]}