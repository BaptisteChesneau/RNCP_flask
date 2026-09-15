import pytest
from app import app as flask_app  # Direct import of the Flask instance
from extensions import db
from models.message import MessageSupport

@pytest.fixture
def client():
    """Fixture to configure the application in testing mode."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # In-memory database
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_messages_non_autorise(client):
    """Verify that an unauthenticated user receives a 403 Forbidden error."""
    response = client.get("/api/messages")
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Non autorisé"

def test_envoi_message_contenu_vide(client):
    """Verify that an empty message returns a 400 Bad Request error."""
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1  # Simulate authenticated user session

    response = client.post("/api/messages", json={
        "contenu": "   "
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Contenu vide"

def test_envoi_et_recuperation_message(client):
    """Verify sending a message (POST) and retrieving it (GET)."""
    # 1. Simulated login session
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Send message (POST)
    response_post = client.post("/api/messages", json={
        "contenu": "Bonjour, j'ai une question sur mon devis.",
        "destinataire_id": 2
    })
    
    assert response_post.status_code == 201
    res_data = response_post.get_json()
    assert res_data["status"] == "success"
    assert "message_id" in res_data

    # 3. Retrieve history (GET)
    response_get = client.get("/api/messages")
    assert response_get.status_code == 200
    
    messages_list = response_get.get_json()
    assert len(messages_list) == 1
    assert messages_list[0]["contenu"] == "Bonjour, j'ai une question sur mon devis."
    assert messages_list[0]["is_me"] is True