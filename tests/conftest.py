import os
import sys
from unittest.mock import MagicMock
import pytest

# 1. Ajoute la racine du projet au path Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2. Force SQLite en mémoire pour SQLAlchemy
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app, db, mongo


@pytest.fixture(scope="module", autouse=True)
def mock_mongo():
    """Simule la base de données MongoDB pour éviter les timeouts vers Scalingo."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    # Simule une liste vide pour .find() et un retour de succès pour les autres opérations
    mock_collection.find.return_value = []
    mock_collection.find_one.return_value = None
    mock_collection.delete_many.return_value = MagicMock(deleted_count=0)
    mock_db.chatbot = mock_collection
    mock_db.admin_users = mock_collection

    mongo.db = mock_db
    yield mock_db


@pytest.fixture(scope="module", autouse=True)
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()