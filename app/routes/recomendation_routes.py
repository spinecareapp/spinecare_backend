from flask import Blueprint, request, jsonify
import pandas as pd
import re
from sklearn.preprocessing import LabelEncoder
import os

rekomendasi_bp = Blueprint("rekomendasi", __name__)

# Ambil path dari file Python saat ini (some_route.py di routes/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Keluar dari "routes" lalu keluar dari "app", kemudian masuk ke "model_weights"
file_path = os.path.join(current_dir, "..", "..", "model_weights", "dataset.csv")

# Pastikan path benar (debugging)
file_path = os.path.abspath(file_path)
print("Dataset Path:", file_path)  # Debugging: cek apakah path benar

# Load dataset
df = pd.read_csv(file_path)

# Konversi semua teks ke lowercase untuk konsistensi
df["keluhan"] = df["keluhan"].str.lower()
df["tingkat_nyeri"] = df["tingkat_nyeri"].astype(str).str.lower()

# Encode tingkat nyeri menggunakan LabelEncoder
le = LabelEncoder()
df["tingkat_nyeri_encoded"] = le.fit_transform(df["tingkat_nyeri"])

# Mapping tingkat nyeri agar sesuai dengan angka 1, 2, 3
mapping_nyeri = {"ringan": "1", "sedang": "2", "berat": "3"}
df["tingkat_nyeri"] = df["tingkat_nyeri"].map(mapping_nyeri)

# Ekstrak angka dari durasi untuk analisis lebih lanjut
df["durasi_angka"] = df["durasi"].apply(
    lambda x: int(re.search(r"\d+", x).group()) if pd.notnull(x) else 0
)


def rekomendasi_gerakan(keluhan_list, tingkat_nyeri, jumlah_rekomendasi=3):
    """
    Memberikan rekomendasi gerakan terapi berdasarkan keluhan (multi-choice) dan tingkat nyeri.
    """
    # Konversi input user ke lowercase
    keluhan_list = [k.lower() for k in keluhan_list]
    tingkat_nyeri = str(tingkat_nyeri).lower()

    # Konversi tingkat nyeri ke skala dataset
    if tingkat_nyeri == "3":  # Tingkat nyeri berat
        filter_tingkat = ["1", "2", "3"]
    elif tingkat_nyeri == "2":  # Tingkat nyeri sedang
        filter_tingkat = ["1", "2"]
    else:  # Tingkat nyeri ringan
        filter_tingkat = ["1"]

    # Debugging
    print("Keluhan yang diterima:", keluhan_list)
    print("Tingkat nyeri setelah konversi:", filter_tingkat)

    # Pencocokan berdasarkan substring (misalnya "nyeri punggung" cocok dengan "nyeri punggung bawah")
    hasil = df[
        (df["tingkat_nyeri"].isin(filter_tingkat))
        & (df["keluhan"].apply(lambda x: any(k in x for k in keluhan_list)))
    ]

    # Jika ada hasil, ambil rekomendasi gerakan
    if not hasil.empty:
        return (
            hasil[["gerakan", "deskripsi", "durasi"]]
            .drop_duplicates()
            .head(jumlah_rekomendasi)
            .to_dict(orient="records")
        )
    else:
        return []


@rekomendasi_bp.route("/recomendation", methods=["POST"])
def get_rekomendasi():
    data = request.get_json()
    keluhan = data.get("keluhan", [])
    tingkat_nyeri = data.get("tingkat_nyeri", "")

    print("Keluhan diterima:", keluhan)
    print("Tingkat nyeri diterima:", tingkat_nyeri)
    print("Data unik di dataset:", df["keluhan"].unique())

    hasil = rekomendasi_gerakan(keluhan, tingkat_nyeri)
    print("Hasil rekomendasi:", hasil)

    return jsonify({"rekomendasi": hasil})
