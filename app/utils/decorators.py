from functools import wraps
from flask import request, jsonify
from app import jwt, db


def api_key_required(func):
    @wraps(func)
    def check_api_key(*args, **kwargs):
        apiKey = request.headers.get("x-api-key")
        print(f"Received API Key: {apiKey}")  # Log API key yang diterima

        if not apiKey:
            return jsonify({"message": "API key is missing"}), 400

        try:
            # Mencari API key di database
            db_api_key = db.db.api_key.find_one({"api_key": apiKey})
            print(f"Database API Key: {db_api_key}")  # Log data yang ditemukan di DB

            # Menangani jika tidak ada API key yang ditemukan
            if db_api_key is None:
                return jsonify({"message": "API key not found in the database"}), 404

            if apiKey == db_api_key["api_key"]:
                return func(*args, **kwargs)
            else:
                return jsonify({"message": "Please provide a correct API key"}), 400
        except Exception as e:
            print(f"Error: {e}")  # Log error
            return jsonify({"message": "Tidak ada token"}), 500

    return check_api_key
