# app/routes/rekomendasi_routes.py
from flask import Blueprint, request, jsonify
from app.services.recomendation_services import (
    delete_history_by_id,
    get_history_by_userId,
    rekomendasi_gerakan,
    simpan_rekomendasi,
)

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
        simpan_rekomendasi(userId, hasil[0], diagnosa)
        return jsonify(hasil[0]), 200
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
