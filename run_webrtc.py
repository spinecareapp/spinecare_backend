from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfigurasi MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/spinemotion_db"
mongo = PyMongo(app)


# Helper untuk mengubah ObjectId ke string (jika diperlukan)
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# === Endpoint baru untuk feedback pain scale ===
@app.route("/feedback", methods=["POST"])
def post_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email")
    date = data.get("date")
    pain = data.get("pain_level")

    # Validasi
    if not email or not date or pain is None:
        return jsonify({"error": "Field email, date, dan pain_level dibutuhkan"}), 400

    try:
        pain = int(pain)
        if pain < 0 or pain > 10:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "pain_level harus integer antara 0 dan 10"}), 400

    # Simpan ke koleksi "feedback"
    feedback_doc = {"email": email, "date": date, "pain_level": pain}
    result = mongo.db.feedback.insert_one(feedback_doc)

    return (
        jsonify(
            {"message": "Feedback received", "feedback_id": str(result.inserted_id)}
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
