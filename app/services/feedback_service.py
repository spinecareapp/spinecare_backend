from app import db  # import PyMongo instance dari app mu
from bson import ObjectId


def simpan_feedback(userId: str, date: str, rekomendasi_id: str, pain_level: int):
    """
    Simpan satu dokumen feedback pain scale ke koleksi `feedback`.
    """
    doc = {
        "userId": userId,
        "date": date,
        "rekomendasi_id": rekomendasi_id,
        "pain_level": pain_level,
    }
    result = db.db.feedback.insert_one(doc)
    return result


def ambil_feedback_by_userId(userId: str):
    cursor = db.db.feedback.find({"userId": userId})
    feedbacks = []
    for doc in cursor:
        # Ambil rekomendasi_id
        rekom_id_str = doc.get("rekomendasi_id")
        rekom_detail = None

        if rekom_id_str:
            try:
                rekom = db.db.recomendation.find_one({"_id": ObjectId(rekom_id_str)})
                if rekom:
                    rekom["_id"] = str(rekom["_id"])
                    rekom_detail = {
                        "arah_latihan": rekom.get("rekomendasi", {}).get(
                            "arah_latihan"
                        ),
                        "gerakan": rekom.get("rekomendasi", {}).get("gerakan", []),
                        "diagnosa": rekom.get("diagnosa", {}),
                        "timestamp": rekom.get("timestamp"),
                    }
            except Exception as e:
                print(f"Error ambil rekomendasi: {e}")

        feedbacks.append(
            {
                "id": str(doc["_id"]),
                "userId": doc["userId"],
                "date": doc["date"],
                "painLevel": doc["pain_level"],
                "rekomendasi_id": rekom_id_str,
                "rekomendasi": rekom_detail,
            }
        )
    return feedbacks
