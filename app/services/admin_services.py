from app import db
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def login_admin(username, password):
    user = db.db.admin.find_one({"username": username, "role": "admin"})

    if not user:
        return None, "Admin tidak ditemukan"

    try:
        if ph.verify(user["password"], password):
            return user, None
        else:
            return None, "Password salah"
    except VerifyMismatchError:
        return None, "Password tidak cocok"
    
def create_admin(username: str, password: str):
    from app import db
    from argon2 import PasswordHasher
    from datetime import datetime

    ph = PasswordHasher()

    if db.db.users.find_one({"username": username}):
        return {"message": "Username sudah digunakan"}, 400

    hashed_password = ph.hash(password)
    datetime_now = datetime.now().strftime("%Y%m%d%H%M%S")

    user = {
        "username": username,
        "password": hashed_password,
        "role": "admin",
        "is_verify": True,
        "created_at": datetime_now,
        "updated_at": datetime_now
    }

    db.db.users.insert_one(user)
    return {"message": "Admin berhasil dibuat"}, 201
    
