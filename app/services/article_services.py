from bson import ObjectId
from flask import current_app, jsonify
from app import db
import datetime
from werkzeug.utils import secure_filename
import os


def add_article_service(data, files):
    try:
        title = data["title"]
        content = data["content"]
        writer = data["writer"]
        source = data["source"]
        photo = files

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_image.jpg"
        path = f"static/uploads/articles/{filename}"
        photo.save(path)

        add_article = {
            "title": title,
            "content": content,
            "writer": writer,
            "source": source,
            "photo": filename,
        }

        db.db.articles.insert_one(add_article)

        return {"message": "Add article success"}, 201
    except Exception as e:
        return {"message": f"Error {e}"}, 500


def get_articles_service():
    articles = db.db.articles.find()

    return jsonify(
        [
            {
                "id": str(article["_id"]),
                "title": article["title"],
                "content": article["content"],
                "writer": article["writer"],
                "photo": article["photo"],
            }
            for article in articles
        ]
    )


def get_article_service(id):
    article = db.db.articles.find_one({"_id": ObjectId(id)})
    if article:
        return {
            "id": str(article["_id"]),
            "title": article["title"],
            "content": article["content"],
            "writer": article["writer"],
            "source": article["source"],
            "photo": article["photo"],
        }, 200
    else:
        return {"message": "Article tidak ditemukan"}


def delete_article_service(id):
    result = db.db.articles.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return {"message": "Article berhasil dihapus"}, 200
    else:
        return {"message": "Article gagal dihapus"}, 404


def update_article_with_file_service(id, data, photo=None):
    update_fields = {
        "title": data["title"],
        "content": data["content"],
        "writer": data["writer"],
        "source": data["source"],
    }

    if photo:
        clean_name = secure_filename(photo.filename)
        filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{clean_name}"

        folder_path = os.path.abspath(
            os.path.join(current_app.root_path, "static", "uploads", "articles")
        )
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, filename)

        print(f"Simpan file ke: {file_path}")
        photo.save(file_path)

        update_fields["photo"] = filename

    db.db.articles.update_one({"_id": ObjectId(id)}, {"$set": update_fields})
    return {"message": "Article updated"}, 200


def update_article_service(id, data):
    title = data["title"]
    content = data["content"]
    writer = data["writer"]
    source = data["source"]

    update_article = {
        "title": title,
        "content": content,
        "writer": writer,
        "source": source,
    }

    db.db.articles.update_one({"_id": ObjectId(id)}, {"$set": update_article})

    return {"message": "Article berhasil diubah"}
