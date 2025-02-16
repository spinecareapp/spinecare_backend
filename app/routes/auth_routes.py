from flask import Blueprint, request, jsonify
from app.services.root_services import hello_world
from app.services.auth_services import register_user, verif_user, login_user
from app.utils.decorators import api_key_required
from flask_jwt_extended import jwt_required

from app import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
@api_key_required
def register():
    data = request.get_json()
    return register_user(data)

@bp.route('/verify_account/<token>', methods=['GET'])
def verify_account(token):
    return verif_user(token)

@bp.route('/login', methods=['POST'])
@api_key_required
def login():
    data = request.headers.get('Authorization')
    return login_user(data)
    



