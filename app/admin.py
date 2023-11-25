from flask_admin.contrib.sqla import ModelView

from app import admin_app
from app.models import *

admin_app.add_view(ModelView(Room, db.session, endpoint='rooms'))
admin_app.add_view(ModelView(Song, db.session))
admin_app.add_view(ModelView(User, db.session))
admin_app.add_view(ModelView(Playlist, db.session))