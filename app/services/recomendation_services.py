import pandas as pd
import os
from datetime import datetime
from app import db
from bson.objectid import ObjectId

# --- DATA LOADING AND PREPARATION ---

# Load the new, more comprehensive dataset
current_dir = os.path.dirname(os.path.abspath(__file__))
# Pastikan nama file CSV sudah sesuai dengan file terbaru Anda
file_path = os.path.abspath(
    os.path.join(current_dir, "..", "..", "model_weights", "dataset-rekomendasi.csv")
)
df = pd.read_csv(file_path, encoding="utf-8-sig")

# --- DATA CLEANING (SANGAT PENTING) ---
# Menyeragamkan nama kolom menjadi huruf kecil
df.columns = df.columns.str.strip().str.lower()

# Menyeragamkan isi data menjadi huruf kecil untuk pencocokan yang konsisten
for col in ["faktor_memperberat", "faktor_memperingan", "durasi", "tingkat_nyeri", "arah_latihan"]:
    df[col] = df[col].astype(str).str.strip().str.lower()

# Memecah 'faktor_memperberat' yang bisa memiliki banyak nilai
df["faktor_memperberat_list"] = df["faktor_memperberat"].apply(
    lambda x: sorted([item.strip() for item in x.split(",")])
)


# --- NEW TWO-STAGE RECOMMENDATION LOGIC ---

def _find_best_match(df_rules, user_inputs):
    """
    Fungsi internal untuk mencari aturan terbaik dari sekumpulan aturan yang sudah difilter.
    Mencari kecocokan sempurna terlebih dahulu, kemudian kecocokan parsial.
    """
    # Prioritas 1: Mencari kecocokan sempurna untuk semua faktor
    perfect_match = df_rules[
        (df_rules["faktor_memperingan"] == user_inputs["pereda"]) &
        (df_rules["durasi"] == user_inputs["durasi"]) &
        (df_rules["tingkat_nyeri"] == user_inputs["nyeri"])
    ]
    if not perfect_match.empty:
        return perfect_match.iloc[0]

    # Prioritas 2: Mencari kecocokan parsial (misal, mengabaikan tingkat nyeri)
    partial_match = df_rules[
        (df_rules["faktor_memperingan"] == user_inputs["pereda"]) &
        (df_rules["durasi"] == user_inputs["durasi"])
    ]
    if not partial_match.empty:
        return partial_match.iloc[0]

    # Jika tidak ada yang cocok sama sekali, kembalikan baris pertama dari aturan yang ada
    if not df_rules.empty:
        return df_rules.iloc[0]
        
    return None


def rekomendasi_gerakan(faktor_memperberat_user, faktor_memperingan_user, durasi_user, skor_nyeri_user):
    """
    Fungsi rekomendasi yang sudah direvisi untuk menerima skor nyeri 1-6.
    """

    # --- PERBAIKAN: Ubah input dari string ke integer ---
    try:
        skor_nyeri_user = int(skor_nyeri_user)
    except (ValueError, TypeError):
        # Jika konversi gagal (misal inputnya bukan angka), beri nilai default aman
        skor_nyeri_user = 1 
    # ---------------------------------------------------
    
    # --- LANGKAH TAMBAHAN: MAP SKOR 1-6 KE KATEGORI ---
    tingkat_nyeri_kategori = ""
    if 1 <= skor_nyeri_user <= 3:  # <-- SEKARANG AMAN, KARENA MEMBANDINGKAN ANGKA DENGAN ANGKA
        tingkat_nyeri_kategori = "ringan"
    elif 4 <= skor_nyeri_user <= 6:
        tingkat_nyeri_kategori = "sedang"
    else:
        tingkat_nyeri_kategori = "ringan" # Fallback
    # ----------------------------------------------------

    # Normalisasi input pengguna
    user_inputs = {
        "pemicu": sorted([x.strip().lower() for x in faktor_memperberat_user]),
        "pereda": faktor_memperingan_user.strip().lower(),
        "durasi": durasi_user.strip().lower(),
        "nyeri": tingkat_nyeri_kategori, # <-- Gunakan variabel kategori yang baru
    }

    # --- TAHAP 1: Tentukan Strategi Utama ---
    # Cari semua aturan yang pemicunya paling cocok dengan input pengguna
    # Logika ini mencari aturan yang semua pemicunya ada di input pengguna
    possible_rules = df[df["faktor_memperberat_list"].apply(
        lambda rule_pemicu: all(item in user_inputs["pemicu"] for item in rule_pemicu)
    )]
    
    # Jika ada aturan yang cocok, cari yang terbaik. Jika tidak, langsung ke default.
    best_rule = None
    if not possible_rules.empty:
        # --- TAHAP 2: Penyesuaian Taktis & Dosis ---
        # Dari kandidat aturan yang ada, cari yang paling cocok berdasarkan faktor sekunder
        best_rule = _find_best_match(possible_rules, user_inputs)

    # --- JARING PENGAMAN: Aturan Default ---
    if best_rule is None:
        # Jika tidak ada aturan spesifik yang cocok, gunakan aturan default yang paling aman
        default_rules = df[df["arah_latihan"] == "mobilisasi/postural"]
        if not default_rules.empty:
            best_rule = default_rules.iloc[0] # Ambil aturan mobilisasi pertama sebagai default
        else:
            # Fallback jika bahkan aturan default tidak ada
            return [] 

    # Format output sesuai standar
    rekomendasi = {
        "arah_latihan": best_rule["arah_latihan"].capitalize(),
        "gerakan": [best_rule["gerakan1"], best_rule["gerakan2"], best_rule["gerakan3"]],
    }
    
    # Fungsi ini mengembalikan satu rekomendasi terbaik dalam sebuah list
    return [rekomendasi]

# --- Fungsi-fungsi lain (simpan, get, delete) tetap sama ---
def simpan_rekomendasi(userId, rekomendasi, diagnosa):
    data = {
        "userId": userId,
        "arah_latihan": rekomendasi["arah_latihan"],
        "gerakan": rekomendasi["gerakan"],
        "diagnosa": diagnosa,
        "timestamp": datetime.now(),
    }
    result = db.db.recomendation.insert_one(data)
    return str(result.inserted_id)

def get_history_by_userId(userId):
    results = db.db.recomendation.find({"userId": userId})
    data = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    return data

def delete_history_by_id(history_id):
    try:
        obj_id = ObjectId(history_id)
        result = db.db.recomendation.delete_one({"_id": obj_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error saat menghapus riwayat: {e}")
        return False



# BACKUP SEBELUM ATURAN BERTINGKAT
# import pandas as pd
# import os
# from datetime import datetime
# from zoneinfo import ZoneInfo
# from app import db
# from bson.objectid import ObjectId  # <-- Tambahkan import ini

# # Load dataset
# current_dir = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.abspath(
#     os.path.join(current_dir, "..", "..", "model_weights", "dataset-rekomendasi.csv")
# )
# df = pd.read_csv(file_path, encoding="utf-8-sig")
# df.columns = df.columns.str.strip().str.lower()

# required_cols = [
#     "faktor_memperberat",
#     "faktor_memperingan",
#     "durasi",
#     "tingkat_nyeri",
#     "arah_latihan",
#     "gerakan1",
#     "gerakan2",
#     "gerakan3",
# ]
# missing = [col for col in required_cols if col not in df.columns]
# if missing:
#     raise Exception(f"Missing columns: {missing}")

# # Normalisasi kolom
# for col in ["faktor_memperberat", "faktor_memperingan", "durasi", "tingkat_nyeri"]:
#     df[col] = df[col].astype(str).str.strip().str.lower()

# df["faktor_memperberat_list"] = df["faktor_memperberat"].apply(
#     lambda x: [item.strip() for item in x.split(",")]
# )


# def rekomendasi_gerakan(
#     faktor_memperberat_user,
#     faktor_memperingan_user,
#     durasi_user,
#     tingkat_nyeri_user,
#     jumlah_rekomendasi=3,
# ):
#     faktor_memperberat_user = [x.strip().lower() for x in faktor_memperberat_user]
#     faktor_memperingan_user = faktor_memperingan_user.strip().lower()
#     durasi_user = durasi_user.strip().lower()
#     tingkat_nyeri_user = tingkat_nyeri_user.strip().lower()

#     hasil = df.copy()
#     hasil = hasil[hasil["tingkat_nyeri"] == tingkat_nyeri_user]
#     hasil = hasil[hasil["durasi"] == durasi_user]
#     hasil = hasil[hasil["faktor_memperingan"] == faktor_memperingan_user]
#     hasil = hasil[
#         hasil["faktor_memperberat_list"].apply(
#             lambda x: any(item in x for item in faktor_memperberat_user)
#         )
#     ]

#     rekomendasi = []
#     for _, row in hasil.iterrows():
#         rekomendasi.append(
#             {
#                 "arah_latihan": row["arah_latihan"].capitalize(),
#                 "gerakan": [row["gerakan1"], row["gerakan2"], row["gerakan3"]],
#             }
#         )
#     return rekomendasi[:jumlah_rekomendasi]

# def simpan_rekomendasi(userId, rekomendasi, diagnosa):
#     data = {
#         "userId": userId,
#         "arah_latihan": rekomendasi["arah_latihan"],
#         "gerakan": rekomendasi["gerakan"],
#         "diagnosa": diagnosa,
#         "timestamp": datetime.now(),
#     }
#     result = db.db.recomendation.insert_one(data)
#     return str(result.inserted_id)


# # --- PERUBAHAN DIMULAI DI SINI ---


# # 1. Mengubah nama fungsi dari get_history_by_email menjadi get_history_by_userId
# def get_history_by_userId(userId):
#     # Query berdasarkan 'userId' karena fungsi simpan_rekomendasi menyimpannya sebagai 'userId'
#     results = db.db.recomendation.find({"userId": userId})
#     data = []
#     for doc in results:
#         doc["_id"] = str(doc["_id"])
#         data.append(doc)
#     return data


# # 2. Menambahkan fungsi delete_history_by_id yang hilang
# def delete_history_by_id(history_id):
#     """
#     Menghapus satu riwayat rekomendasi dari database berdasarkan ID-nya.
#     Menggunakan ObjectId untuk mencari dokumen di MongoDB.
#     """
#     try:
#         # Konversi string id ke ObjectId MongoDB
#         obj_id = ObjectId(history_id)
#         # Hapus dokumen dengan _id yang cocok
#         result = db.db.recomendation.delete_one({"_id": obj_id})
#         # Kembalikan True jika ada 1 dokumen yang terhapus, selain itu False
#         return result.deleted_count > 0
#     except Exception as e:
#         print(f"Error saat menghapus riwayat: {e}")
#         return False
