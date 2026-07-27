from datetime import datetime
from extensions import db, fernet

class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    
    # 🏢 Informations Entreprise (Normes INSEE / DGFiP)
    type_entreprise = db.Column(db.String(20))          # "SARL", "SAS", "EURL", "SASU", "EI", "SCI"
    activite = db.Column(db.String(100))               # Libellé activité
    code_ape = db.Column(db.String(5), nullable=True)   # Norme INSEE NAF (5 char ex: 6920Z)
    siren = db.Column(db.String(9), nullable=True)      # Norme SIREN INSEE (9 chiffres)
    siret = db.Column(db.String(14), nullable=True)     # Norme SIRET INSEE (14 chiffres)
    tva_intracommunautaire = db.Column(db.String(13), nullable=True) # Norme DGFiP / UE (ex: FR12345678901)
    cabinet = db.Column(db.String(100))                 # Raison sociale / Dénomination
    
    # 👤 Contact Principal (Normes RNIPP / Code Civil Français)
    civilite = db.Column(db.String(4))                  # "M." ou "Mme" (4 char max)
    nom = db.Column(db.String(50))                      # Norme INSEE nom (50 max)
    prenom = db.Column(db.String(50))                   # Norme INSEE prénom (50 max)
    
    # 📞 Coordonnées (Normes ARCEP / AFNOR / RGPD)
    email_chiffre = db.Column(db.String(255), unique=True) # E-mail chiffré Fernet (Conforme RGPD)
    telephone = db.Column(db.String(15), nullable=True) # Norme ARCEP / E.164 (+336...)
    adresse_siege = db.Column(db.String(255))           # Norme AFNOR NF Z 10-011
    code_postal = db.Column(db.String(10), nullable=True)# Norme Code Postal France (5) & UE (10 max)
    pays = db.Column(db.String(2), default="FR")        # Norme UE ISO 3166-1 alpha-2 ("FR", "BE", "LU")

    utilisateur = db.relationship("Utilisateur", back_populates="clients")
    utilisateurs_lies = db.relationship("UtilisateurClient", back_populates="client", cascade="all, delete-orphan")

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

    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), primary_key=True)
    date_liaison = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur = db.relationship("Utilisateur", back_populates="clients_lies", passive_deletes=True)
    client = db.relationship("Client", back_populates="utilisateurs_lies", passive_deletes=True)