from flask import jsonify


def hello_world():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>SpineMotion - Sehatkan Tulang Belakang Anda</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                background: linear-gradient(to bottom right, #00cec9, #0984e3);
                color: white;
            }
            .container {
                max-width: 960px;
                margin: 0 auto;
                padding: 60px 30px;
                text-align: center;
            }
            h1 {
                font-size: 3em;
                margin-bottom: 20px;
            }
            p {
                font-size: 1.2em;
                line-height: 1.6;
                margin-bottom: 30px;
            }
            .cta {
                margin-top: 40px;
            }
            .btn {
                background-color: white;
                color: #0984e3;
                padding: 15px 30px;
                border: none;
                border-radius: 30px;
                font-size: 1em;
                cursor: pointer;
                transition: 0.3s;
                text-decoration: none;
            }
            .btn:hover {
                background-color: #dfe6e9;
            }
            .features {
                margin-top: 50px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                text-align: left;
            }
            .feature {
                background-color: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
            }
            footer {
                margin-top: 60px;
                font-size: 0.9em;
                color: #dfe6e9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Spinecare</h1>
            <p><strong>Aplikasi kesehatan tulang belakang Anda.</strong><br>
            Deteksi dini, rekomendasi gerakan, dan edukasi postur untuk hidup lebih sehat tanpa nyeri.</p>
            <div class="cta">
                <a href="/privacy-policy" class="btn">Lihat Kebijakan Privasi</a>
            </div>

            <div class="features">
                <div class="feature">
                    <h3>📷 Deteksi Postur</h3>
                    <p>Gunakan kamera untuk mengidentifikasi keluhan dan postur tidak ideal.</p>
                </div>
                <div class="feature">
                    <h3>📊 Rekomendasi Gerakan</h3>
                    <p>Gerakan seperti plank, stretch, dan yoga untuk pemulihan atau pencegahan.</p>
                </div>
                <div class="feature">
                    <h3>📚 Artikel Edukatif</h3>
                    <p>Dapatkan informasi lengkap seputar nyeri punggung dan gaya hidup sehat.</p>
                </div>
                <div class="feature">
                    <h3>🔐 Aman & Pribadi</h3>
                    <p>Data Anda terenkripsi dan hanya digunakan untuk layanan kesehatan Anda.</p>
                </div>
            </div>

            <footer>
                &copy; 2025 Spinecare. Dibuat dengan cinta dan tulang belakang yang sehat ❤️
            </footer>
        </div>
    </body>
    </html>
    """


def delete_account():
    return """
    <html>
    <head>
        <title>Permintaan Penghapusan Akun - SpineMotion</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 600px;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            h2 {
                color: #343a40;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Permintaan Penghapusan Akun - SpineMotion</h2>
            <p>Jika Anda ingin menghapus akun dan seluruh data Anda, kirim email ke:</p>
            <p><strong>spinemotionapp@gmail.com</strong></p>
            <p>Dengan subjek: <em>Hapus Akun</em></p>
            <p>Kami akan menghapus akun Anda dan seluruh data terkait dalam waktu 7 hari kerja.</p>
        </div>
    </body>
    </html>
    """


def privacy_policy():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>Kebijakan Privasi - SpineMotion</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f6f8;
                color: #333;
                line-height: 1.8;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                background: white;
                padding: 40px 60px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                border-radius: 10px;
            }
            h2 {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 20px;
            }
            h3 {
                color: #2d3436;
                margin-top: 30px;
                font-size: 20px;
            }
            ul {
                margin-top: 0;
                padding-left: 20px;
            }
            p {
                margin: 10px 0;
            }
            strong {
                color: #d63031;
            }
            footer {
                text-align: center;
                margin-top: 40px;
                font-size: 14px;
                color: #888;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Kebijakan Privasi - SpineMotion</h2>
            <p>SpineMotion menghargai privasi Anda. Kebijakan privasi ini menjelaskan bagaimana kami mengumpulkan, menggunakan, dan melindungi informasi pribadi Anda saat menggunakan aplikasi kami.</p>

            <h3>1. Informasi yang Kami Kumpulkan</h3>
            <p>Kami mengumpulkan informasi berikut:</p>
            <ul>
                <li>Nama lengkap</li>
                <li>Alamat email</li>
                <li>Nomor HP</li>
                <li>Jenis kelamin</li>
                <li>Riwayat penggunaan dan hasil analisis postur/tulang belakang</li>
            </ul>

            <h3>2. Penggunaan Informasi</h3>
            <p>Informasi Anda digunakan untuk:</p>
            <ul>
                <li>Memberikan rekomendasi dan laporan kesehatan</li>
                <li>Meningkatkan layanan aplikasi</li>
                <li>Berkomunikasi terkait layanan atau pembaruan aplikasi</li>
            </ul>

            <h3>3. Keamanan Data</h3>
            <p>Semua data dikirim secara terenkripsi dan disimpan dengan aman. Kami tidak membagikan informasi Anda kepada pihak ketiga tanpa izin Anda.</p>

            <h3>4. Hak Anda</h3>
            <p>Anda dapat meminta penghapusan akun dan data pribadi Anda kapan saja dengan mengirim email ke <strong>spinemotionapp@gmail.com</strong>.</p>

            <h3>5. Perubahan Kebijakan</h3>
            <p>Kami dapat memperbarui kebijakan privasi ini dari waktu ke waktu. Perubahan akan diinformasikan melalui aplikasi atau email.</p>

            <footer>
                Terakhir diperbarui: 23 Juni 2025
            </footer>
        </div>
    </body>
    </html>
    """
