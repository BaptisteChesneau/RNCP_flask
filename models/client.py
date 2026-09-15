from datetime import datetime
from extensions import db, fernet

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    activite = db.Column(db.String(100))
    type_entreprise = db.Column(db.String(100))
    cabinet = db.Column(db.String(100))
    civilite = db.Column(db.String(10))
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email_chiffre = db.Column(db.String(500), unique=True)
    adresse_siege = db.Column(db.String(200))

    utilisateur = db.relationship("Utilisateur", back_populates="clients")

    utilisateurs_lies = db.relationship(
        "UtilisateurClient", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client {self.prenom} {self.nom}>"

    @property
    def email(self):
        try:
            return fernet.decrypt(self.email_chiffre.encode()).decode() if fernet else self.email_chiffre
        except Exception:
            return "[erreur de déchiffrement]"

    @email.setter
    def email(self, value):
        if fernet:
            self.email_chiffre = fernet.encrypt(value.encode()).decode()
        else:
            self.email_chiffre = value


class UtilisateurClient(db.Model):
    __tablename__ = "utilisateur_client"

    utilisateur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id", ondelete="CASCADE"),
        primary_key=True,
    )
    client_id = db.Column(
        db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), primary_key=True
    )
    date_liaison = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur = db.relationship(
        "Utilisateur", back_populates="clients_lies", passive_deletes=True
    )
    client = db.relationship(
        "Client", back_populates="utilisateurs_lies", passive_deletes=True
    )