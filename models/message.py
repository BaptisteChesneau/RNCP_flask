from datetime import datetime
from extensions import db


class MessageSupport(db.Model):
    __tablename__ = "messages_support"

    id = db.Column(db.Integer, primary_key=True)
    expediteur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False
    )
    destinataire_id = db.Column(
        db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True
    )  # None = destiné à tout le support/admin
    contenu = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    lu = db.Column(db.Boolean, default=False)

    # Relations
    expediteur = db.relationship(
        "Utilisateur", foreign_keys=[expediteur_id], backref="messages_envoyes"
    )
    destinataire = db.relationship(
        "Utilisateur",
        foreign_keys=[destinataire_id],
        backref="messages_recus",
    )