import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    MONGO_URI = "mongodb://localhost:27017/spinemotion_db"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JET_ACCESS_TOKEN_EXPIRES = os.environ.get("JET_ACCESS_TOKEN_EXPIRES") or timedelta(
        hours=1
    )
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
