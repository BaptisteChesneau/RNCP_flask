from extensions import db

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=True
    )
    sujet = db.Column(db.String(200))
    message = db.Column(db.Text)
    date_creation = db.Column(db.DateTime)
    statut = db.Column(db.String(50))

    utilisateur = db.relationship("Utilisateur", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket #{self.id} - {self.sujet[:15]}...>"


class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))
    utilisateur = db.relationship("Utilisateur", back_populates="historiques")


class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_inscription = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Newsletter {self.email}>"


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime)
    auteur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    auteur = db.relationship("Utilisateur", back_populates="articles")

    def __repr__(self):
        return f"<BlogPost {self.titre[:15]}...>"