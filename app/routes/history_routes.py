from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.history_services import get_history_service, add_history_service
from app.utils.decorators import api_key_required

bp = Blueprint('history', __name__, url_prefix='/history')

@bp.route('/', methods=["POST"])
@jwt_required()
@api_key_required
def add_history():
    data = request.get_json()
    return add_history_service(data)

@bp.route('/', methods=["GET"])
@jwt_required()
@api_key_required
def get_history():
    return get_history_service()
        
