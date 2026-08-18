import pytest
from app import create_app

def test_acces_espace_client_non_connecte():
    """Vérifie qu'un utilisateur non connecté est redirigé vers la page de login."""
    app = create_app()
    client = app.test_client()
    
    # Tentative d'accès à la route /espace-client
    response = client.get('/compte-client', follow_redirects=True)
    
    # Vérifie qu'on est redirigé vers la page de connexion
    assert response.status_code == 200
    assert b"Connexion" in response.data # Vérifie que le mot 'Connexion' est dans la page

def test_soumission_formulaire_devis():
    """Vérifie le bon fonctionnement du formulaire de demande de devis."""
    app = create_app()
    client = app.test_client()
    
    # Simulation de la soumission d'un formulaire
    response = client.post('/devis', data={
        'nom_entreprise': 'ML2C_TEST',
        'montant_estime': '1500'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Demande envoyée".encode('utf-8') in response.data