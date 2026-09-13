import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🗝️ Security Keys
    SECRET_KEY = os.getenv("APP_SECRET_KEY")
    FERNET_KEY = os.getenv("FERNET_KEY")

    # 🗄️ PostgreSQL Database (Scalingo / Local)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🍃 MongoDB Database
    MONGO_URI = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")

    # ✉️ Mail Configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "votre_email@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "votre_mot_de_passe")

    # 🔒 Security & Cookies
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB max limit
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)