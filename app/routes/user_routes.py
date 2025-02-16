from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import api_key_required
from app.services.user_services import get_profile, forgot_password_user, reset_password_view_user, reset_password_user, change_password_user, update_profile_service, verify_otp_service, request_change_email_service, perform_service

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/profile', methods=['GET'])
@jwt_required()
@api_key_required
def profile():
    current_user = get_jwt_identity()
    return get_profile(current_user)

@bp.route('/forgot-password', methods=['POST'])
@api_key_required
def forgot_password_endpoint():
    data = request.get_json()
    print(data)
    return forgot_password_user(data)

@bp.route('/reset-password-view/<token>', methods=['GET'])
def reset_password_view(token):
    return reset_password_view_user(token)

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    password = request.form.get("password")
    confirm_password = request.form.get("confirmPassword")
    email = request.form.get("email")
    return reset_password_user(password, confirm_password, email)

@bp.route('/change-password', methods=['PUT'])
@jwt_required()
@api_key_required
def change_password():
    data = request.get_json()
    return change_password_user(data)

@bp.route('/request-change-email', methods=['POST'])
@jwt_required()
@api_key_required
def change_email():
    data = request.get_json()
    return request_change_email_service(data)

@bp.route('/verify-otp', methods=['PUT'])
@jwt_required()
@api_key_required
def verify_new_email():
    data = request.get_json()
    return verify_otp_service(data)

@bp.route('/update-profile', methods=['PUT'])
@jwt_required()
@api_key_required
def update_profile():
    data = request.form.to_dict()
    
    files=[]
    
    if "photo" in request.files:
        files = request.files["photo"]
        
    return update_profile_service(data, files)

@bp.route('/perform', methods=['GET'])
@jwt_required()
def perform():
    current_user = get_jwt_identity()
    print(current_user)
    return perform_service(current_user)

@bp.route('/image/<image_name>', methods=["GET"])
def get_image(image_name):
    return send_file(f"../static/uploads/profiles/{image_name}", mimetype="image/jpeg")
