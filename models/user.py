from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Utilisateur(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)

    # Relationships with other tables
    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship("Preferences", back_populates="utilisateur", uselist=False)
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")
    parametres = db.relationship("ParametresCompte", back_populates="utilisateur", uselist=False)

    # Direct relationships and relationships via a join table
    clients = db.relationship("Client", back_populates="utilisateur", lazy=True)
    clients_lies = db.relationship(
        "UtilisateurClient", back_populates="utilisateur", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"

    def set_password(self, password):
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe_hash, password)


class ParametresCompte(db.Model):
    __tablename__ = "parametres_compte"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, unique=True
    )

    # Preferences
    langue = db.Column(db.String(10), default="fr")
    theme = db.Column(db.String(10), default="light")
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    # Social media
    facebook = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    instagram = db.Column(db.String(255))

    # Photo
    photo_url = db.Column(db.String(255))

    # Facturation
    nom_facturation = db.Column(db.String(255))
    adresse_facturation = db.Column(db.String(255))

    # Date of update
    date_mise_a_jour = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    utilisateur = db.relationship(
        "Utilisateur", back_populates="parametres"
    )

    def __repr__(self):
        return f"<ParametresCompte utilisateur_id={self.utilisateur_id} langue={self.langue} theme={self.theme}>"


class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )

    langue = db.Column(db.String(10))
    theme = db.Column(db.String(10))
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    utilisateur = db.relationship("Utilisateur", back_populates="preferences")

    def __repr__(self):
        return f"<Preferences #{self.id} - {self.utilisateur_id}>"