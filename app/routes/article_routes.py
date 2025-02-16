from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required
from app.utils.decorators import api_key_required
from app.services.article_services import add_article_service, get_articles_service, get_article_service, delete_article_service, update_article_service

bp = Blueprint('article', __name__, url_prefix='/article')

@bp.route('/', methods=["POST"])
@api_key_required
def add_article():
    data = request.form.to_dict()
    files = request.files["photo"]
    return add_article_service(data, files)

@bp.route('/', methods=["GET"])
@jwt_required()
@api_key_required
def get_articles():
    return get_articles_service() 

@bp.route('/<id>', methods=["GET"])
@jwt_required()
@api_key_required
def get_article(id):
    return get_article_service(id)

@bp.route('/<id>', methods=["DELETE"])
@api_key_required
def delete_article(id):
    return delete_article_service(id)

@bp.route('/<id>', methods=["PUT"])
@api_key_required
def update_article(id):
    data = request.get_json()
    return update_article_service(id, data)
        
@bp.route('/image/<image_name>', methods=["GET"])
def get_image(image_name):
    return send_file(f"../static/uploads/articles/{image_name}", mimetype="image/jpeg")