# app/services/rekomendasi_service.py
import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from app import db

# Load dataset
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.abspath(
    os.path.join(current_dir, "..", "..", "model_weights", "dataset-rekomendasi.csv")
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
    raise Exception(f"Missing columns: {missing}")

# Normalisasi kolom
for col in ["faktor_memperberat", "faktor_memperingan", "durasi", "tingkat_nyeri"]:
    df[col] = df[col].astype(str).str.strip().str.lower()

df["faktor_memperberat_list"] = df["faktor_memperberat"].apply(
    lambda x: [item.strip() for item in x.split(",")]
)


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

    rekomendasi = []
    for _, row in hasil.iterrows():
        rekomendasi.append(
            {
                "arah_latihan": row["arah_latihan"].capitalize(),
                "gerakan": [row["gerakan1"], row["gerakan2"], row["gerakan3"]],
            }
        )
    return rekomendasi[:jumlah_rekomendasi]


def simpan_rekomendasi(email, rekomendasi):
    timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
    db.db.recomendation.insert_one(
        {
            "email": email,
            "timestamp": timestamp,
            "rekomendasi": rekomendasi,
        }
    )


def get_history_by_email(email):
    results = db.db.recomendation.find({"email": email})
    data = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    return data
