import pytest
from app import app as flask_app

@pytest.fixture
def client():
    """Reusable fixture for the Flask test client."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        yield client

def test_acces_espace_client_non_connecte(client):
    """Verify that an unauthenticated user is redirected to the login page."""
    response = client.get('/compte-client', follow_redirects=True)
    
    assert response.status_code == 200
    assert b"connexion" in response.data.lower() or b"connecter" in response.data.lower()

def test_soumission_formulaire_devis(client):
    """Verify that the quote request form submission functions correctly."""
    # 1. Simulate an authenticated user session
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Submit POST form data to /resume-devis with valid fields
    response = client.post('/resume-devis', data={
        'secteur': 'Informatique',
        'nom': 'ML2C_TEST',
        'user_email': 'test@ml2c.com',
        'type_service': 'Tenue Comptable',
        'date_rdv': '2026-09-01',
        'heure_rdv': '10:00'
    }, follow_redirects=True)
    
    # 3. Assert that the server returns a 200 OK status code
    assert response.status_code == 200