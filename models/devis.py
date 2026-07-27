from extensions import db

class Devis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    secteur = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    type_service = db.Column(db.String(100))
    date_rdv = db.Column(db.String(50))
    heure_rdv = db.Column(db.String(50))
    email = db.Column(db.String(120))

    utilisateur = db.relationship("Utilisateur", back_populates="devis")

    def __repr__(self):
        return f"<Devis {self.nom} - {self.type_service}>"


class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    montant = db.Column(db.Float)
    date_transaction = db.Column(db.DateTime)
    statut = db.Column(db.String(50))
    mode_paiement = db.Column(db.String(50))

    utilisateur = db.relationship("Utilisateur", back_populates="paiements")

    def __repr__(self):
        return f"<Paiement #{self.id} - {self.statut}>"