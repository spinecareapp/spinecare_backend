from app import db  # import PyMongo instance dari app mu


def simpan_feedback(email: str, date: str, daftarGerakan: str, pain_level: int):
    """
    Simpan satu dokumen feedback pain scale ke koleksi `feedback`.
    """
    doc = {
        "email": email,
        "date": date,
        "daftar_gerakan": daftarGerakan,
        "pain_level": pain_level,
    }
    result = db.db.feedback.insert_one(doc)
    return result


def ambil_feedback_by_email(email: str):
    """
    Ambil semua feedback berdasarkan email dari koleksi `feedback`.
    """
    cursor = db.db.feedback.find({"email": email})
    feedbacks = []
    for doc in cursor:
        feedbacks.append(
            {
                "id": str(doc["_id"]),
                "email": doc["email"],
                "date": doc["date"],
                "painLevel": doc["pain_level"],
            }
        )
    return feedbacks
