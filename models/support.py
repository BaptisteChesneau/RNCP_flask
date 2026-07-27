from extensions import db

class SupportTicket(db.Model):
    __tablename__ = "support_ticket"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)
    sujet = db.Column(db.String(200))
    message = db.Column(db.Text)                        # Type Text
    date_creation = db.Column(db.DateTime, default=db.func.now())
    statut = db.Column(db.String(20), default="nouveau")# "nouveau", "en_cours", "resolu"

    utilisateur = db.relationship("Utilisateur", back_populates="support_tickets")


class Historique(db.Model):
    __tablename__ = "historique"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))

    utilisateur = db.relationship("Utilisateur", back_populates="historiques")


class Newsletter(db.Model):
    __tablename__ = "newsletter"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False) # Norme RGPD
    date_inscription = db.Column(db.DateTime, default=db.func.now())


class BlogPost(db.Model):
    __tablename__ = "blog_post"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime, default=db.func.now())
    auteur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    auteur = db.relationship("Utilisateur", back_populates="articles")