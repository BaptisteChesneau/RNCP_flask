import os
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from flask_migrate import Migrate
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet

# Extension instances initialization
db = SQLAlchemy()
mongo = PyMongo()
migrate = Migrate()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

# Fernet Key (used for encrypting/decrypting sensitive data such as client email addresses)
fernet_key = os.environ.get("FERNET_KEY")
fernet = Fernet(fernet_key.encode()) if fernet_key else None