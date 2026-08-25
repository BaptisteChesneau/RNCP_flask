import pytest
from app import app as flask_app  # Import direct de l'instance Flask
from extensions import db
from models.message import MessageSupport

@pytest.fixture
def client():
    """Fixture pour configurer l'application en mode test."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Base en mémoire
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_messages_non_autorise(client):
    """Vérifie qu'un utilisateur non authentifié reçoit une erreur 403."""
    response = client.get("/api/messages")
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Non autorisé"

def test_envoi_message_contenu_vide(client):
    """Vérifie qu'un message vide renvoie une erreur 400."""
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1  # Simulation utilisateur connecté

    response = client.post("/api/messages", json={
        "contenu": "   "
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Contenu vide"

def test_envoi_et_recuperation_message(client):
    """Vérifie l'envoi d'un message (POST) puis sa récupération (GET)."""
    # 1. Connexion simulée
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Envoi du message (POST)
    response_post = client.post("/api/messages", json={
        "contenu": "Bonjour, j'ai une question sur mon devis.",
        "destinataire_id": 2
    })
    
    assert response_post.status_code == 201
    res_data = response_post.get_json()
    assert res_data["status"] == "success"
    assert "message_id" in res_data

    # 3. Récupération de l'historique (GET)
    response_get = client.get("/api/messages")
    assert response_get.status_code == 200
    
    messages_list = response_get.get_json()
    assert len(messages_list) == 1
    assert messages_list[0]["contenu"] == "Bonjour, j'ai une question sur mon devis."
    assert messages_list[0]["is_me"] is True