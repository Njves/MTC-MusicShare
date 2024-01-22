import io

from flask import url_for


def test_upload(db_session, app):
    data = {'attach_file': (io.BytesIO(), 'test.jpg')}
    response = app.test_client().post(url_for('chat.upload_file'), data=data, content_type='multipart/form-data')
