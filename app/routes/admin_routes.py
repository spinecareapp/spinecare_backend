from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.admin_services import login_admin
from app.services.article_services import update_article_with_file_service
from app.utils.decorators import admin_login_required
from app import db  # ✅ import db agar bisa query ke Mongo
from bson import ObjectId  # ✅ untuk manipulasi _id dari MongoDB
import datetime
import os

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder=os.path.abspath("app/admin/templates")
)

# ✅ LOGIN
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print("POST /admin/login dipanggil")
        print("Username:", username)
        print("Password:", password)

        user, error = login_admin(username, password)

        print("User:", user)
        print("Error:", error)

        if user:
            session['admin_id'] = str(user['_id'])
            session['username'] = user['username']
            print("Session setelah login:", session)
            return redirect(url_for('admin.dashboard'))
        else:
            flash(error or 'Login gagal.')

    return render_template('login.html')

# ✅ DASHBOARD
@admin_bp.route('/dashboard')
@admin_login_required
def dashboard():
     # Hitung total user dari koleksi `users`
    total_users = db.db.users.count_documents({})
    total_articles = db.db.articles.count_documents({})
    total_detections = db.db.detections.count_documents({})
    total_jenis_gerakan = len(db.db.detections.distinct("namaGerakan"))

    # Ambil daftar user (misalnya 10 teratas)
    users = list(db.db.users.find().sort('created_at', -1).limit(10))
    return render_template('index.html', total_users=total_users, users=users, total_articles=total_articles, total_detections=total_detections, total_jenis_gerakan=total_jenis_gerakan)

@admin_bp.route('/table')
@admin_login_required
def table():
    return render_template('forms.html')

@admin_bp.route('/articles')
@admin_login_required
def admin_articles():
    articles = list(db.db.articles.find().sort('_id', -1))
    return render_template('articles.html', articles=articles)

@admin_bp.route('/articles/add', methods=['POST'])
@admin_login_required
def add_article_admin():
    title = request.form['title']
    content = request.form['content']
    writer = request.form['writer']
    source = request.form['source']
    photo = request.files.get('photo')

    filename = None
    if photo:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{photo.filename}"
        UPLOAD_FOLDER = "app/static/uploads/articles"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        photo.save(os.path.join(UPLOAD_FOLDER, filename))

    article = {
        "title": title,
        "content": content,
        "writer": writer,
        "source": source,
        "photo": filename
    }
    db.db.articles.insert_one(article)
    flash("Artikel berhasil ditambahkan", "success")
    return redirect(url_for('admin.admin_articles'))

@admin_bp.route('/articles/edit/<id>', methods=['POST'])
@admin_login_required
def edit_article_admin(id):
    data = request.form.to_dict()
    photo = request.files.get('photo')
    update_article_with_file_service(id, data, photo)
    flash("Artikel berhasil diperbarui", "success")
    return redirect(url_for('admin.admin_articles'))

@admin_bp.route('/articles/delete/<id>')
@admin_login_required
def delete_article_admin(id):
    db.db.articles.delete_one({'_id': ObjectId(id)})
    flash("Artikel berhasil dihapus", "success")
    return redirect(url_for('admin.admin_articles'))

@admin_bp.route('/users/delete/<user_id>')
@admin_login_required
def delete_user(user_id):
    from app import db
    result = db.db.users.delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count:
        flash("User berhasil dihapus", "success")
    else:
        flash("User gagal dihapus atau tidak ditemukan", "danger")
    return redirect(url_for('admin.dashboard'))


# ✅ LOGOUT
@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))
