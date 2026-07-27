import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db, Utilisateur
from werkzeug.security import generate_password_hash  

def setup_test_user():
    with app.app_context():
        
        user = Utilisateur.query.filter_by(email="test@example.com").first()

        if not user:
            
            user = Utilisateur(
                nom_utilisateur="test_user",
                email="test@example.com",
            )

            user.mot_de_passe_hash = generate_password_hash(
                "Password123!", method="scrypt"
            )

            db.session.add(user)
            db.session.commit()

def test_login_valid_credentials():
    setup_test_user()

    with app.test_client() as client:
        response = client.post(
            "/login",
            data=dict(
                email="test@example.com",
                password="Password123!",  
            ),
            follow_redirects=True,
        )
    
        assert response.status_code == 200
        assert "Email ou mot de passe invalide".encode("utf-8") in response.data


def test_login_invalid_credentials():
    with app.test_client() as client:
        response = client.post(
            "/login",
            data=dict(
                email="wrong@example.com",
                password="wrongpass",
            ),
            follow_redirects=True,
        )
        
        assert response.status_code == 200
        assert b"Email ou mot de passe invalide" in response.data

