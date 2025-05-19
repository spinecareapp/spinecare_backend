# app/__init__.py
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_socketio import SocketIO

db = PyMongo()
jwt = JWTManager()
mail = Mail()
socketio = SocketIO()

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    socketio.init_app(app)
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # ⬇ import route DI DALAM fungsi
    from app.routes import (
        root_routes,
        auth_routes,
        user_routes,
        history_routes,
        socketio_routes,
        recomendation_routes,
        admin_routes,
        article_routes  # ⬅ dipindah ke sini
    )

    # Register routes
    app.register_blueprint(root_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(article_routes.bp)
    app.register_blueprint(history_routes.bp)
    app.register_blueprint(socketio_routes.bp)
    app.register_blueprint(recomendation_routes.rekomendasi_bp)
    app.register_blueprint(admin_routes.admin_bp)

    return app
