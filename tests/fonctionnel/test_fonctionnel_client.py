import pytest
from app import app as flask_app

@pytest.fixture
def client():
    """Fixture réutilisable pour le client de test Flask."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_acces_espace_client_non_connecte(client):
    """Vérifie qu'un utilisateur non connecté est redirigé vers la page de login."""
    response = client.get('/compte-client', follow_redirects=True)
    
    assert response.status_code == 200
    # Recherche insensible à la casse ou mot-clé plus global
    assert b"connexion" in response.data.lower() or b"connecter" in response.data.lower()

def test_soumission_formulaire_devis(client):
    """Vérifie le bon fonctionnement du formulaire de demande de devis."""
    # 1. Simuler un utilisateur connecté
    with client.session_transaction() as sess:
        sess["utilisateur_id"] = 1

    # 2. Envoyer le formulaire en POST
    response = client.post('/devis', data={
        'nom_entreprise': 'ML2C_TEST',
        'montant_estime': '1500'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Demande envoy" in response.data