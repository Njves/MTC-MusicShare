from flask_admin.contrib.sqla import ModelView

from app import admin_app
from app.models import *

class SecurityModelView(ModelView):
    column_display_pk = True
    def is_accessible(self):
        # TODO: Добавить проверку
        return True

admin_app.add_view(SecurityModelView(Message, db.session))
admin_app.add_view(SecurityModelView(Attachment, db.session))
admin_app.add_view(SecurityModelView(Room, db.session))
admin_app.add_view(SecurityModelView(User, db.session))