from extensions import db

class Devis(db.Model):
    __tablename__ = "devis"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    
    secteur = db.Column(db.String(100))
    nom = db.Column(db.String(50))                      # Norme INSEE nom (50 max)
    type_service = db.Column(db.String(100))
    date_rdv = db.Column(db.String(10))                 # Format normé ISO 8601 : "AAAA-MM-JJ"
    heure_rdv = db.Column(db.String(5))                 # Format normé : "HH:MM"
    email = db.Column(db.String(255))                   # Norme RGPD / UE

    utilisateur = db.relationship("Utilisateur", back_populates="devis")


class Paiement(db.Model):
    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    montant = db.Column(db.Float)                       # Montant en EUR (€)
    date_transaction = db.Column(db.DateTime, default=db.func.now())
    statut = db.Column(db.String(20))                  # "valide", "en_attente", "refuse"
    mode_paiement = db.Column(db.String(20))           # "Stripe", "PayPal", "Virement"

    utilisateur = db.relationship("Utilisateur", back_populates="paiements")