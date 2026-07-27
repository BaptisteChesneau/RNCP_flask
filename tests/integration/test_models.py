from extensions import db
from models.user import Utilisateur
from models.client import Client, UtilisateurClient
from models.devis import Devis
from models.support import SupportTicket

def test_crud_models(client):
    # 1. Création Utilisateur
    user = Utilisateur(nom_utilisateur="test_model_user", email="test_model@ml2c.fr")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    assert user.id is not None

    # 2. Création Client
    c = Client(utilisateur_id=user.id, nom="Durand", prenom="Claire", type_entreprise="SARL")
    c.email = "claire.durand@example.fr"
    db.session.add(c)
    db.session.commit()
    assert Client.query.filter_by(nom="Durand").first() is not None

    # 3. Association UtilisateurClient
    liaison = UtilisateurClient(utilisateur_id=user.id, client_id=c.id)
    db.session.add(liaison)
    db.session.commit()
    assert UtilisateurClient.query.filter_by(utilisateur_id=user.id, client_id=c.id).first() is not None

    # 4. Devis & Support
    ticket = SupportTicket(utilisateur_id=user.id, sujet="Test", message="Message test")
    devis = Devis(utilisateur_id=user.id, nom="Devis Test", type_service="Conseil")
    db.session.add_all([ticket, devis])
    db.session.commit()
    assert SupportTicket.query.filter_by(utilisateur_id=user.id).first() is not None
    assert Devis.query.filter_by(nom="Devis Test").first() is not None