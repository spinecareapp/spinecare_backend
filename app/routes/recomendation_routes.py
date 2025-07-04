# app/routes/rekomendasi_routes.py
from flask import Blueprint, request, jsonify
from app.services.recomendation_services import (
    delete_history_by_id,
    get_history_by_userId,
    rekomendasi_gerakan,
    simpan_rekomendasi,
)
from bson import ObjectId
from app import db

bp = Blueprint("rekomendasi", __name__)


@bp.route("/recomendation", methods=["POST"])
def get_rekomendasi():
    data = request.get_json()
    userId = data.get("userId")
    faktor_memperberat = data.get("faktor_memperberat", [])
    faktor_memperingan = data.get("faktor_memperingan", "")
    durasi = data.get("durasi", "")
    tingkat_nyeri = data.get("tingkat_nyeri", "")

    if not userId:
        return jsonify({"error": "userId harus disertakan"}), 400

    hasil = rekomendasi_gerakan(
        faktor_memperberat, faktor_memperingan, durasi, tingkat_nyeri
    )
    if hasil:
        diagnosa = {
            "faktor_memperberat": faktor_memperberat,
            "faktor_memperingan": faktor_memperingan,
            "durasi": durasi,
            "tingkat_nyeri": tingkat_nyeri,
        }
        rekomendasi_id = simpan_rekomendasi(userId, hasil[0], diagnosa)
        response = hasil[0]
        response["id"] = rekomendasi_id  # tambahkan ID ke respons
        return jsonify(response), 200
    else:
        return jsonify({"message": "Tidak ada rekomendasi ditemukan"}), 404


@bp.route("/historyrecomendation", methods=["GET"])
def get_history():
    userId = request.args.get("userId")
    if not userId:
        return jsonify({"error": "Parameter userId dibutuhkan"}), 400

    data = get_history_by_userId(userId)
    return jsonify(data), 200


@bp.route("/historyrecomendation/<id>", methods=["DELETE"])
def delete_history(id):
    try:
        deleted = delete_history_by_id(id)
        if deleted:
            return jsonify({"message": "Riwayat berhasil dihapus"}), 200
        else:
            return jsonify({"error": "Riwayat tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/rekomendasi/<rekomendasi_id>", methods=["GET"])
def get_rekomendasi_by_id(rekomendasi_id):
    try:
        obj_id = ObjectId(rekomendasi_id)
    except:
        return jsonify({"error": "ID tidak valid"}), 400

    rekom = db.db.recomendation.find_one({"_id": obj_id})
    if not rekom:
        return jsonify({"error": "Rekomendasi tidak ditemukan"}), 404

    # Convert ObjectId fields to string
    rekom["_id"] = str(rekom["_id"])

    # Jika ada field ObjectId lain dalam rekomendasi (misal userId), convert juga
    if "userId" in rekom and isinstance(rekom["userId"], ObjectId):
        rekom["userId"] = str(rekom["userId"])

    return jsonify({"rekomendasi": rekom}), 200
