import pytest
from app import create_app
from extensions import db
from models.message import MessageSupport

@pytest.fixture
def client():
    """Fixture to configure the application in test mode."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # In-memory database for tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_messages_non_autorise(client):
    """Verifies that an unauthenticated user receives a 403 error."""
    response = client.get("/api/messages") # Adjust blueprint prefix if needed
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Non autorisé"

def test_envoi_message_contenu_vide(client):
    """Verifies that an empty message content returns a 400 error."""
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1  # Simulates a logged-in user

    response = client.post("/api/messages", json={
        "contenu": "   "  # Empty content or whitespace
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Contenu vide"

def test_envoi_et_recuperation_message(client):
    """Verifies successful message sending (POST) followed by its retrieval (GET)."""
    # 1. Simulate client login
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Send a message (POST)
    response_post = client.post("/api/messages", json={
        "contenu": "Bonjour, j'ai une question sur mon devis.",
        "destinataire_id": 2
    })
    
    assert response_post.status_code == 201
    res_data = response_post.get_json()
    assert res_data["status"] == "success"
    assert "message_id" in res_data

    # 3. Retrieve message history (GET)
    response_get = client.get("/api/messages")
    assert response_get.status_code == 200
    
    messages_list = response_get.get_json()
    assert len(messages_list) == 1
    assert messages_list[0]["contenu"] == "Bonjour, j'ai une question sur mon devis."
    assert messages_list[0]["is_me"] is True