import sys, os
from getpass import getpass
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from argon2 import PasswordHasher

# Load .env dan tambahkan ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

# Ambil URI dari env
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
print(f"✅ MONGO_URI yang digunakan: {mongo_uri}")  # << CETAK DI SINI

# Akses database dan koleksi admin
db = client.spinemotion_db
admin_collection = db.admin

ph = PasswordHasher()

print("== Buat Akun Admin ==")
username = input("Username admin: ")
password = getpass("Password: ")
confirm = getpass("Ulangi password: ")

if password != confirm:
    print("❌ Password tidak cocok.")
    sys.exit()

if admin_collection.find_one({"username": username}):
    print("❌ Username sudah digunakan.")
    sys.exit()

hashed_password = ph.hash(password)
datetime_now = datetime.now().strftime("%Y%m%d%H%M%S")

admin = {
    "username": username,
    "password": hashed_password,
    "role": "admin",
    "is_verify": True,
    "created_at": datetime_now,
    "updated_at": datetime_now
}

admin_collection.insert_one(admin)
print("✅ Admin berhasil dibuat.")
