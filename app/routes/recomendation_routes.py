from flask import Blueprint, request, jsonify
import pandas as pd
import os

rekomendasi_bp = Blueprint("rekomendasi", __name__)

# Ambil path file dataset
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.abspath(os.path.join(current_dir, "..", "..", "model_weights", "dataset_rekomendasi.csv"))
print("Dataset Path:", file_path)

# Load CSV dan normalisasi kolom
df = pd.read_csv(file_path, encoding='utf-8-sig')
df.columns = df.columns.str.strip().str.lower()
print("Kolom dalam dataset:", df.columns.tolist())

# List kolom yang wajib ada
required_cols = [
    'faktor memperberat', 'faktor memperingan', 'durasi', 'tingkat nyeri',
    'gerakan 1', 'gerakan 2', 'gerakan 3'
]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise Exception(f"Kolom berikut TIDAK ADA di dataset: {missing}")

# Normalisasi nilai teks
for col in ['faktor memperberat', 'faktor memperingan', 'durasi', 'tingkat nyeri']:
    df[col] = df[col].astype(str).str.strip().str.lower()

# Pisahkan faktor memperberat jadi list jika ada lebih dari 1
df['faktor_memperberat_list'] = df['faktor memperberat'].apply(lambda x: [item.strip() for item in x.split(",")])

def rekomendasi_gerakan(faktor_memperberat_user, faktor_memperingan_user, durasi_user, tingkat_nyeri_user, jumlah_rekomendasi=3):
    faktor_memperberat_user = [x.strip().lower() for x in faktor_memperberat_user]
    faktor_memperingan_user = faktor_memperingan_user.strip().lower()
    durasi_user = durasi_user.strip().lower()
    tingkat_nyeri_user = tingkat_nyeri_user.strip().lower()

    hasil = df.copy()
    hasil = hasil[hasil['tingkat nyeri'] == tingkat_nyeri_user]
    hasil = hasil[hasil['durasi'] == durasi_user]
    hasil = hasil[hasil['faktor memperingan'] == faktor_memperingan_user]
    hasil = hasil[hasil['faktor_memperberat_list'].apply(lambda x: any(item in x for item in faktor_memperberat_user))]

    if not hasil.empty:
        rekomendasi = []
        for _, row in hasil.iterrows():
            rekomendasi.append({
                "gerakan": [row["gerakan 1"], row["gerakan 2"], row["gerakan 3"]]
            })
        return rekomendasi[:jumlah_rekomendasi]
    else:
        return []

@rekomendasi_bp.route("/recomendation", methods=["POST"])
def get_rekomendasi():
    data = request.get_json()
    faktor_memperberat = data.get("faktor_memperberat", [])
    faktor_memperingan = data.get("faktor_memperingan", "")
    durasi = data.get("durasi", "")
    tingkat_nyeri = data.get("tingkat_nyeri", "")

    print("Input diterima:")
    print("- Faktor memperberat:", faktor_memperberat)
    print("- Faktor memperingan:", faktor_memperingan)
    print("- Durasi:", durasi)
    print("- Tingkat nyeri:", tingkat_nyeri)

    hasil = rekomendasi_gerakan(faktor_memperberat, faktor_memperingan, durasi, tingkat_nyeri)
    return jsonify({"rekomendasi": hasil})
