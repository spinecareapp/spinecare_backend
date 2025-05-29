from app import db  # import PyMongo instance dari app mu

def simpan_feedback(email: str, date: str, pain_level: int):
    """
    Simpan satu dokumen feedback pain scale ke koleksi `feedback`.
    """
    doc = {
        "email": email,
        "date": date,
        "pain_level": pain_level
    }
    result = db.db.feedback.insert_one(doc)
    return result
