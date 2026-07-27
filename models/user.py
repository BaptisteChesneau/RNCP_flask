from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Utilisateur(db.Model, UserMixin):
    __tablename__ = "utilisateur"

    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(30), unique=True, nullable=False) # Pseudo (30 char max)
    email = db.Column(db.String(255), unique=True, nullable=False)           # Conforme RGPD / e-mail UE
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)           # Hash sécurisé PBKDF2

    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relations
    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship("Preferences", back_populates="utilisateur", uselist=False)
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")

    clients = db.relationship("Client", back_populates="utilisateur", lazy=True)
    clients_lies = db.relationship("UtilisateurClient", back_populates="utilisateur", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"

    def set_password(self, password):
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe_hash, password)


class ParametresCompte(db.Model):
    __tablename__ = "parametres_compte"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, unique=True)

    langue = db.Column(db.String(2), default="fr")     # Norme UE / ISO 639-1 ("fr", "en")
    theme = db.Column(db.String(10), default="light")
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    facebook = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    instagram = db.Column(db.String(255))

    photo_url = db.Column(db.String(255))
    nom_facturation = db.Column(db.String(100))
    adresse_facturation = db.Column(db.String(255))   # Norme AFNOR NF Z 10-011

    date_mise_a_jour = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    utilisateur = db.relationship("Utilisateur", backref=db.backref("parametres_compte", uselist=False))


class Preferences(db.Model):
    __tablename__ = "preferences"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    langue = db.Column(db.String(2), default="fr")     # Norme UE ISO 639-1
    theme = db.Column(db.String(10), default="light")
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    utilisateur = db.relationship("Utilisateur", back_populates="preferences")