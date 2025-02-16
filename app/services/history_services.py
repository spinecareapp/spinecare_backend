from datetime import datetime
from flask import jsonify
from app import db
from flask_jwt_extended import get_jwt_identity

def get_history_service():
    email = get_jwt_identity()
    user = db.db.users.find_one({"email": email})
    user_id = str(user["_id"])
    histories = db.db.history.find({"user_id": user_id})
    
    return jsonify([{
        "id": str(history["_id"]),
        "date": history["date"],
        "movement": history["movement"]
    } for history in histories]), 200
    
def add_history_service(data):
    email = get_jwt_identity()
    
    user = db.db.users.find_one({"email": email})
    if not user:
        return {
            "message": "Pengguna tidak ditemukan"
        }, 404
    
    date = datetime.now().strftime("%Y%m%d%H%M%S")
    movement = data["movement"]
    
    
    user_id = str(user["_id"])
    
    add_history = {
        "user_id": user_id,
        "email": email,
        "date": date,
        "movement": movement
    }
    
    db.db.history.insert_one(add_history)
    
    return {
        "message": "history berhasil ditambah"
    }, 201
    
    