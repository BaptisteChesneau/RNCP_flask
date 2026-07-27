import os
import sys
import pytest

# 1. Ajoute la racine du projet au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2. Force la variable d'environnement pour que Config charge SQLite en test
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app, db


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