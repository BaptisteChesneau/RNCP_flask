# ===============================================================
#  IMPORTS & CONFIGURATION GLOBALE
# ===============================================================

import io
import base64
import os
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from cryptography.fernet import Fernet
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import pytest
from bs4 import BeautifulSoup

load_dotenv()

# ===============================================================
#  FLASK APP INITIALISATION
# ===============================================================

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

#       COOKIE SECURITY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

#       RATE LIMITING
limiter = Limiter(get_remote_address, app=app,
                  default_limits=["200 per day", "50 per hour"])

#       SIZE LIMIT
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# ===============================================================
#  FLASK-MAIL CONFIG
# ===============================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "votre_email@gmail.com"
app.config["MAIL_PASSWORD"] = "votre_mot_de_passe"

# ===============================================================
#  DATABASE CONFIG (POSTGRES + MONGO)
# ===============================================================

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config["MONGO_URI"] = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")
mongo = PyMongo(app)

fernet = Fernet(os.environ.get("FERNET_KEY").encode())

mail = Mail(app)

# ===============================================================
#  DATABASE MODELS
# ===============================================================

# ---- CLIENT ----
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
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

    @property
    def email(self):
        try:
            return fernet.decrypt(self.email_chiffre.encode()).decode()
        except Exception:
            return "[erreur de déchiffrement]"

    @email.setter
    def email(self, value):
        self.email_chiffre = fernet.encrypt(value.encode()).decode()


# ---- HISTORIQUE ----
class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))
    utilisateur = db.relationship("Utilisateur", back_populates="historiques")


# ---- UTILISATEUR ----
class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)

    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship("Preferences", back_populates="utilisateur", uselist=False)
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")
    parametres = db.relationship("ParametresCompte", back_populates="utilisateur", uselist=False)
    clients = db.relationship("Client", back_populates="utilisateur", lazy=True)
    clients_lies = db.relationship("UtilisateurClient", back_populates="utilisateur",
                                   cascade="all, delete-orphan")

    def set_password(self, password):
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe_hash, password)


# ---- DEVIS ----
class Devis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    secteur = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    type_service = db.Column(db.String(100))
    date_rdv = db.Column(db.String(50))
    heure_rdv = db.Column(db.String(50))
    email = db.Column(db.String(120))

    utilisateur = db.relationship("Utilisateur", back_populates="devis")


# ---- PAIEMENT ----
class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    montant = db.Column(db.Float)
    date_transaction = db.Column(db.DateTime)
    statut = db.Column(db.String(50))
    mode_paiement = db.Column(db.String(50))

    utilisateur = db.relationship("Utilisateur", back_populates="paiements")


# ---- NEWSLETTER ----
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_inscription = db.Column(db.DateTime)


# ---- SUPPORT ----
class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)
    sujet = db.Column(db.String(200))
    message = db.Column(db.Text)
    date_creation = db.Column(db.DateTime)
    statut = db.Column(db.String(50))

    utilisateur = db.relationship("Utilisateur", back_populates="support_tickets")


# ---- PREFERENCES ----
class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    langue = db.Column(db.String(10))
    theme = db.Column(db.String(10))
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    utilisateur = db.relationship("Utilisateur", back_populates="preferences")


# ---- PARAMETRES COMPTE ----
class ParametresCompte(db.Model):
    __tablename__ = "parametres_compte"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, unique=True
    )

    langue = db.Column(db.String(10), default="fr")
    theme = db.Column(db.String(10), default="light")
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    facebook = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    instagram = db.Column(db.String(255))

    photo_url = db.Column(db.String(255))
    nom_facturation = db.Column(db.String(255))
    adresse_facturation = db.Column(db.String(255))
    date_mise_a_jour = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    utilisateur = db.relationship(
        "Utilisateur", backref=db.backref("parametres_compte", uselist=False)
    )


# ---- LIAISON UTILISATEUR / CLIENT ----
class UtilisateurClient(db.Model):
    __tablename__ = "utilisateur_client"

    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True
    )
    client_id = db.Column(
        db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), primary_key=True
    )
    date_liaison = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur = db.relationship("Utilisateur", back_populates="clients_lies",
                                  passive_deletes=True)
    client = db.relationship("Client", back_populates="utilisateurs_lies",
                             passive_deletes=True)


# ---- BLOG ----
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime)
    auteur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    auteur = db.relationship("Utilisateur", back_populates="articles")

# ===============================================================
#  ROUTES PRINCIPALES DU SITE
# ===============================================================

@app.route("/")
@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/header")
def header():
    return render_template("header.html")

@app.route("/footer")
def footer():
    return render_template("footer.html")

@app.route("/plateforme-client")
def plateforme_client():
    return render_template("plateforme_client.html")

@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/notre-histoire")
def notre_histoire():
    return render_template("notre_histoire.html")

@app.route("/notre-equipe")
def notre_equipe():
    return render_template("notre_equipe.html")

@app.route("/rgpd")
def rgpd():
    return render_template("rgpd.html")

@app.route("/mentions-legales")
def mentions_legales():
    return render_template("mentions_legales.html")

@app.route("/atelier")
def atelier():
    return render_template("atelier.html")

@app.route("/nos-outils")
def nos_outils():
    return render_template("nos_outils.html")

@app.route("/nous-contacter")
def nous_contacter():
    return render_template("contact.html")

@app.route("/aide")
def aide():
    return render_template("aide.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")


# ===============================================================
#  AUTHENTIFICATION (LOGIN / SIGNUP / LOGOUT)
# ===============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and utilisateur.check_password(password):
            session["utilisateur_id"] = utilisateur.id
            session["email"] = utilisateur.email
            session["prenom"] = utilisateur.nom_utilisateur

            flash("Connexion réussie !", "success")
            return redirect(url_for("compte_client"))

        flash("Email ou mot de passe invalide.", "danger")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
@app.route("/inscription", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        user = Utilisateur(nom_utilisateur=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["utilisateur_id"] = user.id
        session["email"] = user.email
        session["prenom"] = username

        return redirect(url_for("formulaire_client"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("menu"))


# ===============================================================
#  FORMULAIRE CLIENT
# ===============================================================

@app.route("/formulaire", methods=["GET", "POST"])
def formulaire_client():
    utilisateur_id = session.get("utilisateur_id")

    if not utilisateur_id:
        flash("Vous devez être connecté pour remplir ce formulaire.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        activite = request.form.get("activite")
        type_entreprise = request.form.get("type_entreprise")
        cabinet = request.form.get("cabinet")
        civilite = request.form.get("civilite")
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        adresse_siege = request.form.get("adresse_siege")

        nouveau_client = Client(
            utilisateur_id=utilisateur_id,
            activite=activite,
            type_entreprise=type_entreprise,
            cabinet=cabinet,
            civilite=civilite,
            nom=nom,
            prenom=prenom,
            email=email,
            adresse_siege=adresse_siege,
        )
        db.session.add(nouveau_client)
        db.session.commit()

        return redirect(url_for("confirmation"))

    return render_template("formulaire_client.html")

@app.route("/confirmation")
def confirmation():
    return "Formulaire soumis avec succès ! Merci."


# ===============================================================
#  DEVIS (FORMULAIRE + RESUME + ENVOI AU COMPTE)
# ===============================================================

@app.route("/devis")
def devis():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder au formulaire de devis.", "warning")
        return redirect(url_for("login"))
    return render_template("devis.html")


@app.route("/resume-devis", methods=["POST"])
def resume_devis():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour consulter le résumé.", "warning")
        return redirect(url_for("login"))

    utilisateur_id = session.get("utilisateur_id")

    secteur = request.form.get("secteur")
    nom = request.form.get("nom")
    type_service = request.form.get("type_service")
    date_rdv = request.form.get("date_rdv")
    heure_rdv = request.form.get("heure_rdv")
    form_email = request.form.get("user_email")

    nouveau_devis = Devis(
        utilisateur_id=utilisateur_id,
        secteur=secteur,
        nom=nom,
        type_service=type_service,
        date_rdv=date_rdv,
        heure_rdv=heure_rdv,
        email=form_email,
    )

    db.session.add(nouveau_devis)
    db.session.commit()

    return render_template(
        "resume_devis.html",
        secteur=secteur,
        nom=nom,
        type_service=type_service,
        date_rdv=date_rdv,
        heure_rdv=heure_rdv,
    )


@app.route("/envoyer_compte")
def envoyer_compte():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")

    if not utilisateur_id or not devis_data:
        flash("Erreur : données manquantes.", "danger")
        return redirect(url_for("login"))

    nouveau_devis = Devis(
        utilisateur_id=utilisateur_id,
        secteur=devis_data.get("secteur"),
        nom=devis_data.get("nom"),
        type_service=devis_data.get("type_service"),
        date_rdv=devis_data.get("date_rdv"),
        heure_rdv=devis_data.get("heure_rdv"),
        email=devis_data.get("email"),
    )

    db.session.add(nouveau_devis)
    db.session.commit()

    flash("Le devis a été ajouté à votre compte.", "success")
    return redirect(url_for("compte_client"))


# ===============================================================
#  COMPTE CLIENT / FICHES / PARAMÈTRES / CARTE BANCAIRE
# ===============================================================

@app.route("/compte-client")
def compte_client():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")

    clients = []
    devis_list = []

    if utilisateur_id:
        clients = Client.query.filter_by(utilisateur_id=utilisateur_id).all()
        devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()

    return render_template(
        "compte_client.html",
        clients=clients,
        devis_data=devis_data,
        devis_list=devis_list,
    )


@app.route("/ajouter-carte-test")
def ajouter_carte_test():
    session["carte_bancaire"] = {
        "nom": "Jean Dupont",
        "numero": "4242424242424242",
        "expiration": "12/26",
    }
    return redirect(url_for("compte_client"))


@app.route("/supprimer-carte", methods=["POST"])
def supprimer_carte():
    session.pop("carte_bancaire", None)
    flash("Votre carte a été supprimée.", "success")
    return redirect(url_for("parametres"))


@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    user = {
        "prenom": session.get("prenom", ""),
        "nom": session.get("nom", ""),
        "email": session.get("email", ""),
    }
    return render_template("parametres.html", user=user)



@app.route("/ma-fiche-client")
def ma_fiche_client():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour voir votre fiche client.", "warning")
        return redirect(url_for("login"))

    clients = Client.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("ma_fiche_client.html", clients=clients)


@app.route("/modifier-client/<int:client_id>", methods=["GET", "POST"])
def modifier_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == "POST":
        client.activite = request.form.get("activite")
        client.type_entreprise = request.form.get("type_entreprise")
        client.cabinet = request.form.get("cabinet")
        client.civilite = request.form.get("civilite")
        client.nom = request.form.get("nom")
        client.prenom = request.form.get("prenom")
        client.email = request.form.get("email")
        client.adresse_siege = request.form.get("adresse_siege")

        db.session.commit()
        flash("Fiche mise à jour.", "success")
        return redirect(url_for("ma_fiche_client"))

    return render_template("modifier_client.html", client=client)


@app.route("/supprimer-client/<int:client_id>", methods=["POST"])
def supprimer_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Fiche client supprimée.", "danger")
    return redirect(url_for("ma_fiche_client"))

# ===============================================================
#  SUPPORT CLIENT
# ===============================================================

@app.route("/contact_support", methods=["POST"])
def contact_support():
    subject = request.form.get("subject")
    message = request.form.get("message")
    email = session.get("email", "non connecté")

    print("\n===== SUPPORT MESSAGE =====")
    print(f"Email: {email}")
    print(f"Sujet: {subject}")
    print(f"Message: {message}")
    print("===========================\n")

    flash("Votre message a été envoyé.", "success")
    return redirect(url_for("parametres"))

# ===============================================================
#  CHATBOT UTILISATEUR
# ===============================================================

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    latest_question = None
    latest_reponse = None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            from markupsafe import escape
            question = escape(question)

            user_name = session.get("prenom", "Cher utilisateur")
            reponse = f"Merci {user_name}, nous reviendrons vers vous rapidement."

            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
            flash("Votre question a été envoyée !", "success")

            return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())

    return render_template("chatbot.html", messages=messages)

# ===============================================================
#  ADMIN CHATBOT
# ===============================================================

@app.route("/login-admin", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = mongo.db.admin_users.find_one({"username": username})

        if not admin or not check_password_hash(admin["password"], password):
            flash("Identifiants invalides ❌", "danger")
            return redirect(url_for("login_admin"))

        session["admin_logged_in"] = True
        flash("Connexion réussie", "success")
        return redirect(url_for("admin_chatbot"))

    return render_template("login_admin.html")


@app.route("/admin-chatbot")
def admin_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    messages = list(mongo.db.chatbot.find())
    return render_template("admin_chatbot.html", messages=messages)


@app.route("/modifier-reponse/<message_id>", methods=["POST"])
def modifier_reponse(message_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))

    nouvelle_reponse = request.form.get("reponse")
    mongo.db.chatbot.update_one({"_id": ObjectId(message_id)},
                                {"$set": {"reponse": nouvelle_reponse}})
    return redirect(url_for("admin_chatbot"))


@app.route("/supprimer-message/<message_id>", methods=["POST"])
def supprimer_message(message_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))

    mongo.db.chatbot.delete_one({"_id": ObjectId(message_id)})
    return redirect(url_for("admin_chatbot"))


@app.route("/logout-admin")
def logout_admin():
    session.pop("admin_logged_in", None)
    flash("Déconnecté.", "success")
    return redirect(url_for("login_admin"))


# ===============================================================
#  SÉCURITÉ / ERREURS / UTILITAIRES
# ===============================================================

@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


@app.route("/forcetest500")
def forcetest500():
    raise Exception("Erreur volontaire pour test 500")


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


# ===============================================================
#  LANCEMENT APP
# ===============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

