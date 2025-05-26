# app/routes/rekomendasi_routes.py
from flask import Blueprint, request, jsonify
from app.services.recomendation_services import (
    rekomendasi_gerakan,
    simpan_rekomendasi,
    get_history_by_email,
)

rekomendasi_bp = Blueprint("rekomendasi", __name__)


@rekomendasi_bp.route("/recomendation", methods=["POST"])
def get_rekomendasi():
    data = request.get_json()
    email = data.get("email")
    faktor_memperberat = data.get("faktor_memperberat", [])
    faktor_memperingan = data.get("faktor_memperingan", "")
    durasi = data.get("durasi", "")
    tingkat_nyeri = data.get("tingkat_nyeri", "")

    if not email:
        return jsonify({"error": "Email harus disertakan"}), 400

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
        simpan_rekomendasi(email, hasil[0], diagnosa)
        return jsonify(hasil[0]), 200
    else:
        return jsonify({"message": "Tidak ada rekomendasi ditemukan"}), 404


@rekomendasi_bp.route("/historyrecomendation", methods=["GET"])
def get_history():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Parameter email dibutuhkan"}), 400

    data = get_history_by_email(email)
    return jsonify(data), 200
