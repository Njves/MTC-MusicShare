from flask import Blueprint
import os

bp = Blueprint('site', __name__)


from app.site import routes
