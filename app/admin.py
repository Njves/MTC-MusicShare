from flask import redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app import admin_app, db


class SecurityModelView(sqla.ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


class UserAdmin(SecurityModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    column_display_pk = True
    form_columns = ['username', 'email', 'password_hash', 'color', 'last_seen', 'room_owner', 'messages']


from app.models import User, Message, Room, Attachment

admin_app.add_view(UserAdmin(User, db.session))
admin_app.add_view(SecurityModelView(Message, db.session))
admin_app.add_view(SecurityModelView(Room, db.session))
admin_app.add_view(SecurityModelView(Attachment, db.session))
