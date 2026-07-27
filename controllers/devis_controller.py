from extensions import db
from models.devis import Devis

def creer_devis(utilisateur_id, form_data):
    nouveau_devis = Devis(
        utilisateur_id=utilisateur_id,
        secteur=form_data.get("secteur"),
        nom=form_data.get("nom"),
        type_service=form_data.get("type_service"),
        date_rdv=form_data.get("date_rdv"),
        heure_rdv=form_data.get("heure_rdv"),
        email=form_data.get("user_email"),
    )
    db.session.add(nouveau_devis)
    db.session.commit()
    return nouveau_devis

def supprimer_devis_utilisateur(utilisateur_id, devis_id):
    if not devis_id:
        return False, "Aucun devis sélectionné."
    
    devis = Devis.query.filter_by(id=devis_id, utilisateur_id=utilisateur_id).first()
    if devis:
        db.session.delete(devis)
        db.session.commit()
        return True, "Le devis a été supprimé avec succès."
    return False, "Ce devis n'existe pas ou ne vous appartient pas."