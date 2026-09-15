import pytest
from app import app, db
from models.user import Utilisateur

def setup_test_user():
    user = Utilisateur.query.filter_by(email="test@example.com").first()
    if not user:
        user = Utilisateur(
            nom_utilisateur="testuser",
            email="test@example.com"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    return user

def test_login_valid_credentials(client):
    with app.app_context():
        setup_test_user()
    
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Connexion" in response.data or b"compte" in response.data

def test_login_invalid_credentials(client):
    response = client.post(
        "/login",
        data={"email": "wrong@example.com", "password": "wrongpassword"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"invalide" in response.data.lower()