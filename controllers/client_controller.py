from extensions import db
from models.client import Client

def enregistrer_client(utilisateur_id, form_data):
    nouveau_client = Client(
        utilisateur_id=utilisateur_id,
        activite=form_data.get("activite"),
        type_entreprise=form_data.get("type_entreprise"),
        cabinet=form_data.get("cabinet"),
        civilite=form_data.get("civilite"),
        nom=form_data.get("nom"),
        prenom=form_data.get("prenom"),
        email=form_data.get("email"),
        adresse_siege=form_data.get("adresse_siege"),
    )
    db.session.add(nouveau_client)
    db.session.commit()
    return nouveau_client

def mettre_a_jour_client(client_id, form_data):
    client = Client.query.get_or_404(client_id)
    client.activite = form_data.get("activite")
    client.type_entreprise = form_data.get("type_entreprise")
    client.cabinet = form_data.get("cabinet")
    client.civilite = form_data.get("civilite")
    client.nom = form_data.get("nom")
    client.prenom = form_data.get("prenom")
    client.email = form_data.get("email")
    client.adresse_siege = form_data.get("adresse_siege")
    db.session.commit()
    return client

def supprimer_un_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()