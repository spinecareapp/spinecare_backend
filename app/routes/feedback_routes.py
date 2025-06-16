from flask import Blueprint, request, jsonify
from app.services.feedback_service import ambil_feedback_by_userId, simpan_feedback

bp = Blueprint("feedback", __name__)


@bp.route("/feedback", methods=["POST"])
def post_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    userId = data.get("userId")
    date = data.get("date")
    daftar_gerakan = data.get("daftar_gerakan", [])
    pain = data.get("pain_level")

    if not userId or not date or pain is None:
        return jsonify({"error": "Fields email, date, pain_level dibutuhkan"}), 400

    try:
        pain = int(pain)
        if not (0 <= pain <= 10):
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "pain_level harus integer 0–10"}), 400

    result = simpan_feedback(userId, date, daftar_gerakan, pain)
    return (
        jsonify(
            {"message": "Feedback received", "feedback_id": str(result.inserted_id)}
        ),
        201,
    )


@bp.route("/feedback", methods=["GET"])
def get_feedback():
    userId = request.args.get("userId")
    if not userId:
        return jsonify({"error": "Parameter userId diperlukan"}), 400

    feedbacks = ambil_feedback_by_userId(userId)
    return jsonify(feedbacks), 200
