from flask import Blueprint
admin = Blueprint('admin', __name__)
from app.admin import routes       # noqa
from app.admin import game_routes  # noqa
