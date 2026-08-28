import pytest
from app import app as flask_app

@pytest.fixture
def client():
    """Fixture réutilisable pour le client de test Flask."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        yield client

def test_acces_espace_client_non_connecte(client):
    """Vérifie qu'un utilisateur non connecté est redirigé vers la page de login."""
    response = client.get('/compte-client', follow_redirects=True)
    
    assert response.status_code == 200
    assert b"connexion" in response.data.lower() or b"connecter" in response.data.lower()

def test_soumission_formulaire_devis(client):
    """Vérifie le bon fonctionnement de la soumission du formulaire de devis."""
    # 1. Simuler un utilisateur connecté en session
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Envoyer le formulaire en POST sur /resume-devis avec les bons champs
    response = client.post('/resume-devis', data={
        'secteur': 'Informatique',
        'nom': 'ML2C_TEST',
        'user_email': 'test@ml2c.com',
        'type_service': 'Tenue Comptable',
        'date_rdv': '2026-09-01',
        'heure_rdv': '10:00'
    }, follow_redirects=True)
    
    # 3. Vérifier que la réponse renvoie un code 200 OK
    assert response.status_code == 200