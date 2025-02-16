# Spinemotion Backend

Backend Untuk aplikasi spinemotion. Spinemotion merupakan aplikasi mobile untuk mendeteksi gerakan olahraga untuk mencegah postur bungkuk pada remaja.

## Daftar Isi

- [Fitur](#fitur)
- [Instalasi](#instalasi)
- [API Dokumentasi](#api-dokumentasi)

## Fitur

- **Autentikasi pengguna**: Registrasi, login, dan manajemen pengguna.
- **CRUD Artikel**: Buat, baca, perbarui, dan hapus artikel.
- **Model Deteksi Gerakan**: Dibangun dengan mediapipe dan klasifikasi menggunakan random forest, serta di deploy menggunakan socketio.
- **Visualisasi Performa Pengguna**: Visualisasi performa pengguna dengan menggunakan streamlit

## Instalasi

Berikut adalah langkah-langkah untuk menginstal proyek ini di lingkungan lokal Anda.
**Gunakan Python 3.9**

1. **Clone repositori ini**
   ```bash
   git clone https://github.com/itsmearss/spinemotion-backend.git
   ```
2. **Masuk ke direktori proyek**
   ```bash
   cd spinemotion-backend-main
   ```
3. **Buat dan aktifkan virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. **Instal dependensi menggunakan pip**
   ```bash
   pip install -r requirements.txt
   ```
5. **Salin file `.env.example` menjadi `.env`**
   ```bash
   cp .env.example .env
   ```
6. **Atur konfigurasi database di file `.env`**
   ```bash
   SECRET_KEY=secret key
   MONGO_URI=url mongodb
   JWT_SECRET_KEY=jwt secret key
   JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=1)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=465
   MAIL_USE_SSL=True
   MAIL_USERNAME=gmail
   MAIL_PASSWORD=app password gmail
   ```
7. **Jalankan aplikasi**
   ```bash
   python run.py
   ```

## Dokumentasi API

Untuk dokumentasi lengkap tentang API yang disediakan oleh proyek ini, kunjungi tautan berikut:
[Spinemotion Backend API Documentation](https://documenter.getpostman.com/view/26426683/2sA3e5eoMB)
