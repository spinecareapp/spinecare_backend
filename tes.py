from flask import Flask
from flask_pymongo import PyMongo

# Inisialisasi Flask
app = Flask(__name__)

# Konfigurasi MongoDB dengan Flask-PyMongo
app.config["MONGO_URI"] = "mongodb://localhost:27017/sp_db"
mongo = PyMongo(app)

# Menggunakan Flask App Context agar bisa menggunakan mongo.db di luar route Flask
with app.app_context():
    # Verifikasi apakah API Key ada di dalam koleksi
    api_key = mongo.db.api_key.find_one(
        {
            "api_key": "763ca8a11759c50fff3071bdb81b3282e4bb3906425e04507f393caf48d116e518bb01e469e8ed4ecc3671368bb5b9cd5a2f99aaf830f8bb56d588cb306763a5"
        }
    )
    print(api_key)  # Cek apakah data API key ditemukan
