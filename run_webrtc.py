from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfigurasi MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/spinemotion_db"
mongo = PyMongo(app)


# Helper untuk mengubah ObjectId ke string
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# Endpoint untuk GET data rekomendasi berdasarkan email
@app.route("/api/history", methods=["GET"])
def get_history():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Parameter email dibutuhkan"}), 400

    collection = mongo.db.recomendation
    results = collection.find({"email": email})
    data = [serialize_doc(doc) for doc in results]

    return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)
