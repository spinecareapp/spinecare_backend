from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import os

# === 1. Koneksi MongoDB Lokal ===
client = MongoClient("mongodb://localhost:27017/")
db = client["spinemotion_db"]  # Ganti nama DB sesuai yang kamu pakai

# === 2. Load Dataset CSV ===
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.abspath(
    os.path.join(current_dir, "model_weights", "dataset-rekomendasi.csv")
)

df = pd.read_csv(file_path, encoding="utf-8-sig")
df.columns = df.columns.str.strip().str.lower()

required_cols = [
    "faktor_memperberat",
    "faktor_memperingan",
    "durasi",
    "tingkat_nyeri",
    "arah_latihan",
    "gerakan1",
    "gerakan2",
    "gerakan3",
]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise Exception(f"Kolom berikut TIDAK ADA di dataset: {missing}")

# Normalisasi
for col in [
    "faktor_memperberat",
    "faktor_memperingan",
    "durasi",
    "tingkat_nyeri",
    "arah_latihan",
]:
    df[col] = df[col].astype(str).str.strip().str.lower()

df["faktor_memperberat_list"] = df["faktor_memperberat"].apply(
    lambda x: [item.strip() for item in x.split(",")]
)


# === 3. Fungsi Logika Rekomendasi ===
def rekomendasi_gerakan(
    faktor_memperberat_user,
    faktor_memperingan_user,
    durasi_user,
    tingkat_nyeri_user,
    jumlah_rekomendasi=3,
):
    faktor_memperberat_user = [x.strip().lower() for x in faktor_memperberat_user]
    faktor_memperingan_user = faktor_memperingan_user.strip().lower()
    durasi_user = durasi_user.strip().lower()
    tingkat_nyeri_user = tingkat_nyeri_user.strip().lower()

    hasil = df.copy()
    hasil = hasil[hasil["tingkat_nyeri"] == tingkat_nyeri_user]
    hasil = hasil[hasil["durasi"] == durasi_user]
    hasil = hasil[hasil["faktor_memperingan"] == faktor_memperingan_user]
    hasil = hasil[
        hasil["faktor_memperberat_list"].apply(
            lambda x: any(item in x for item in faktor_memperberat_user)
        )
    ]

    if not hasil.empty:
        rekomendasi = []
        for _, row in hasil.iterrows():
            rekomendasi.append(
                {
                    "arah_latihan": row["arah_latihan"].capitalize(),
                    "gerakan": [row["gerakan1"], row["gerakan2"], row["gerakan3"]],
                }
            )
        return rekomendasi[:jumlah_rekomendasi]
    else:
        return []


# === 4. Setup Flask App ===
app = Flask(__name__)


@app.route("/recomendation", methods=["POST"])
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
        rekomendasi_pertama = hasil[0]
        timestamp_wib = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()

        db.recomendation.insert_one(
            {
                "email": email,
                "timestamp": timestamp_wib,
                "rekomendasi": rekomendasi_pertama,
            }
        )
        return jsonify(rekomendasi_pertama)
    else:
        return jsonify({"message": "Tidak ada rekomendasi ditemukan"}), 404


# === 5. Jalankan App ===
if __name__ == "__main__":
    app.run(debug=True, port=5001)
