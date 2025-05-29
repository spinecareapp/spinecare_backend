from flask import Blueprint, request, jsonify
from services.feedback_service import simpan_feedback

feedback_bp = Blueprint("feedback_bp", __name__)


@feedback_bp.route("/feedback", methods=["POST"])
def post_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email")
    date = data.get("date")
    pain = data.get("pain_level")

    if not email or not date or pain is None:
        return jsonify({"error": "Fields email, date, pain_level dibutuhkan"}), 400

    try:
        pain = int(pain)
        if not (0 <= pain <= 10):
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "pain_level harus integer 0–10"}), 400

    result = simpan_feedback(email, date, pain)
    return (
        jsonify(
            {"message": "Feedback received", "feedback_id": str(result.inserted_id)}
        ),
        201,
    )
