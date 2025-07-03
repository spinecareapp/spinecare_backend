from flask import Blueprint, render_template, request, jsonify
from app.services.root_services import delete_account, hello_world, privacy_policy

bp = Blueprint("dasar", __name__, url_prefix="/")


@bp.route("/", methods=["GET"])
def landing_page():
    return hello_world()


@bp.route("/delete-account", methods=["GET"])
def delete():
    return delete_account()


@bp.route("/privacy-policy", methods=["GET"])
def privacy():
    return privacy_policy()
