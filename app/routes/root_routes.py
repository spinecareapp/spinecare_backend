from flask import Blueprint, request, jsonify
from app.services.root_services import hello_world

bp = Blueprint('dasar', __name__, url_prefix='/')

@bp.route('/', methods=['GET'])
def hello():
    return hello_world()
