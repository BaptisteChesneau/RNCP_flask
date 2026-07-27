from models.user import Utilisateur
from models.client import Client

def test_password_hashing():
    user = Utilisateur(nom_utilisateur="test_user", email="test@ml2c.fr")
    user.set_password("MonMotDePasse123")
    
    assert user.mot_de_passe_hash != "MonMotDePasse123"
    assert user.check_password("MonMotDePasse123") is True
    assert user.check_password("FauxMotDePasse") is False

def test_client_email_encryption():
    client = Client(nom="Dupont", prenom="Jean")
    email_original = "jean.dupont@ml2c.fr"
    
    client.email = email_original
    assert client.email_chiffre != email_original
    assert client.email == email_original