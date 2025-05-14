import os

from dotenv import load_dotenv
from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

load_dotenv()  # ✅ Charge les variables depuis .env
from datetime import datetime
from typing import Any

import pytest
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
# Clé secrète nécessaire pour la session

# Limit file size (e.g. 2 MB max)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# ✅ Dossier d'upload sécurisé et extensions autorisées
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
UPLOAD_FOLDER = os.path.join("static", "uploads")

# Initialisation de Flask-Limiter
limiter = Limiter(
    get_remote_address, app=app, default_limits=["200 per day", "50 per hour"]
)

csrf = CSRFProtect(app)  # ✅ Sécurité anti-CSRF activée ici

# ================== CONFIG FLASK-MAIL ===================
app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Exemple : Gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "votre_email@gmail.com"
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
# For a cleaner use, you can also define:
# app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

# Replace with your exact URL Scalingo
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 🔵 MongoDB configuration for Flask-PyMongo
app.config["MONGO_URI"] = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")
mongo = PyMongo(app)

db: SQLAlchemy = SQLAlchemy(app)
migrate = Migrate(app, db)

# Sécurité des cookies de session
app.config["SESSION_COOKIE_HTTPONLY"] = True  # empêche l'accès JavaScript aux cookies
app.config["SESSION_COOKIE_SECURE"] = (
    True  # nécessite HTTPS pour les cookies (⚠️ à désactiver en dev si pas de HTTPS)
)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # limite les envois cross-site


# =================== MODÈLES ======================
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
    email = db.Column(db.String(120), unique=True)
    adresse_siege = db.Column(db.String(200))

    utilisateur = db.relationship("Utilisateur", back_populates="clients")

    def __repr__(self):
        return f"<Client {self.prenom} {self.nom}>"


class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)

    # Relationships with other tables :
    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship(
        "Preferences", back_populates="utilisateur", uselist=False
    )
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")

    # Relationship: a user can have several customers
    clients = db.relationship("Client", back_populates="utilisateur", lazy=True)

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur}>"

    def set_password(self, password: str) -> None:
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return bool(check_password_hash(self.mot_de_passe_hash, password))


# =================== MODÈLE DEVIS (optionnel) ======================
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

    # Relation: a Quotation belongs to a User
    utilisateur = db.relationship("Utilisateur", back_populates="devis")

    def __repr__(self):
        return f"<Devis {self.nom} - {self.type_service}>"


# =================== MODÈLE PAIEMENT (optionnel) ======================
class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    montant = db.Column(db.Float)  # e.g. 49.99
    date_transaction = db.Column(
        db.DateTime
    )  # May require “from datetime import datetime”.
    statut = db.Column(db.String(50))  # “validated”, “pending”, “refused”, ...
    mode_paiement = db.Column(db.String(50))  # “Stripe”, “PayPal”, ...

    # Relation: a Payment belongs to a User
    utilisateur = db.relationship("Utilisateur", back_populates="paiements")

    def __repr__(self):
        return f"<Paiement #{self.id} - {self.statut}>"


# =================== MODÈLE NEWSLETTER (optionnel) ======================
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_inscription = db.Column(db.DateTime)  # Optional, if you want to save the date

    def __repr__(self):
        return f"<Newsletter {self.email}>"


# =================== MODÈLE SUPPORT TICKET (optionnel) ======================
class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=True
    )
    sujet = db.Column(db.String(200))
    message = db.Column(db.Text)
    date_creation = db.Column(db.DateTime)
    statut = db.Column(db.String(50))  # "nouveau", "en cours", "résolu", ...

    # Relationship: a ticket can belong to a user (or not, if anonymous)
    utilisateur = db.relationship("Utilisateur", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket #{self.id} - {self.sujet[:15]}...>"


# =================== MODÈLE PREFERENCES (optionnel) ======================
class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )

    # Example of columns
    langue = db.Column(db.String(10))  # "FR", "EN", ...
    theme = db.Column(db.String(10))  # "light", "dark"...
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    # Relationship: 1:1 with User (or 1:N according to your logic)
    utilisateur = db.relationship("Utilisateur", back_populates="preferences")

    def __repr__(self):
        return f"<Preferences #{self.id} - {self.utilisateur_id}>"


# =================== MODÈLE HISTORIQUE (optionnel) ======================
class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    path = db.Column(db.String(200))  # URL/Route visitée
    date_visite = db.Column(db.DateTime)  # Date/Heure de la visite

    # Relation: a history belongs to a user
    utilisateur = db.relationship("Utilisateur", back_populates="historiques")

    def __repr__(self):
        return f"<Historique {self.path} - {self.date_visite}>"


# =================== MODÈLE BLOGPOST (optionnel) ======================
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime)
    auteur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    # Relation: a blog post is written by a user
    auteur = db.relationship("Utilisateur", back_populates="articles")

    def __repr__(self):
        return f"<BlogPost {self.titre[:15]}...>"


mail = Mail(app)


@app.route("/header")
def header():
    return render_template("header.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/footer")
def footer():
    return render_template("footer.html")


@app.route("/plateforme-client")
def plateforme_client():
    return render_template("plateforme_client.html")


@app.route("/formulaire", methods=["GET", "POST"])
def formulaire_client() -> Any:
    utilisateur_id = session.get("utilisateur_id")
    print(
        "DEBUG >>> utilisateur_id dans session :", utilisateur_id
    )  # 👈 à supprimer en prod
    if not utilisateur_id:
        flash("Vous devez être connecté pour remplir ce formulaire.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Recovery of form data (secured)
        activite = escape(request.form.get("activite"))
        type_entreprise = escape(request.form.get("type_entreprise"))
        cabinet = escape(request.form.get("cabinet"))
        civilite = escape(request.form.get("civilite"))
        nom = escape(request.form.get("nom"))
        prenom = escape(request.form.get("prenom"))
        email = escape(request.form.get("email"))
        adresse_siege = escape(request.form.get("adresse_siege"))

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

        msg = Message(
            subject="Nouvelle fiche client",
            sender=app.config["MAIL_USERNAME"],
            recipients=["destinataire@example.com"],
            body=f"""
            Activité: {activite}
            Type d'entreprise: {type_entreprise}
            Cabinet: {cabinet}
            Civilité: {civilite}
            Nom: {nom}
            Prénom: {prenom}
            Email: {email}
            Adresse siège: {adresse_siege}
            """,
        )
        # mail.send(msg)

        return redirect(url_for("confirmation"))

    return render_template("formulaire_client.html")


@app.route("/confirmation")
def confirmation():
    return "Formulaire soumis avec succès ! Merci."


@app.route("/devis", methods=["GET"])
def devis():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder au formulaire de devis.", "warning")
        return redirect(url_for("login"))

    # Displays the appointment form
    return render_template("devis.html")


MAX_DEVIS_PAR_UTILISATEUR = 1  # Maximum number of quotes per user


@app.route("/resume-devis", methods=["POST"])
def resume_devis():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour consulter le résumé du devis.", "warning")
        return redirect(url_for("login"))

    utilisateur_id = session.get("utilisateur_id")
    nombre_devis = Devis.query.filter_by(utilisateur_id=utilisateur_id).count()
    if nombre_devis >= 3:
        flash(
            "Vous avez déjà soumis le nombre maximum de devis autorisé (3).", "danger"
        )
        return redirect(url_for("compte_client"))

    secteur = escape(request.form.get("secteur"))
    nom = escape(request.form.get("nom"))
    type_service = escape(request.form.get("type_service"))
    date_rdv = escape(request.form.get("date_rdv"))
    heure_rdv = escape(request.form.get("heure_rdv"))
    form_email = escape(request.form.get("user_email"))

    client_email = session.get("email")
    if client_email and form_email != client_email:
        flash(
            "L'adresse e-mail renseignée ne correspond pas à celle de votre compte client.",
            "danger",
        )
        return redirect(url_for("devis"))

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


@app.route("/envoyer_mail")
def envoyer_mail():
    return "Fonction d'envoi par mail ici"


@app.route("/envoyer_compte")
def envoyer_compte():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")

    if not utilisateur_id or not devis_data:
        flash(
            "Erreur : utilisateur non connecté ou données du devis manquantes.",
            "danger",
        )
        return redirect(url_for("login"))

    # Vérifie si un devis identique a déjà été créé pour cet utilisateur
    devis_existant = Devis.query.filter_by(
        utilisateur_id=utilisateur_id,
        nom=devis_data.get("nom"),
        type_service=devis_data.get("type_service"),
        date_rdv=devis_data.get("date_rdv"),
        heure_rdv=devis_data.get("heure_rdv"),
        email=devis_data.get("email"),
    ).first()

    if devis_existant:
        flash("Ce devis a déjà été enregistré.", "info")
    else:
        # Créer et enregistrer un nouveau devis
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
        flash("Le devis a été enregistré avec succès dans votre compte.", "success")

    return redirect(url_for("compte_client"))


@app.route("/paiement-stripe", methods=["GET", "POST"])
def paiement_stripe():
    if request.method == "POST":
        # Récupérer les champs
        card_holder_name = request.form.get("card_holder_name")
        card_number = request.form.get("card_number")
        card_expiry = request.form.get("card_expiry")
        card_cvv = request.form.get("card_cvv")
        # ... Traiter / Vérifier / Appeler l'API Stripe ...
        return "Paiement Stripe effectué (simulation)."
    return render_template("paiement_stripe.html")


@app.route("/paiement-paypal", methods=["GET", "POST"])
def paiement_paypal():
    if request.method == "POST":
        # Récupérer les champs
        card_holder_name = request.form.get("card_holder_name")
        card_number = request.form.get("card_number")
        card_expiry = request.form.get("card_expiry")
        card_cvv = request.form.get("card_cvv")
        # ... Traiter / Vérifier / Appeler l'API PayPal ...
        return "Paiement PayPal effectué (simulation)."
    return render_template("paiement_paypal.html")


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


@limiter.limit("5 per minute")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = escape(request.form.get("email"))
        password = request.form.get(
            "password"
        )  # Le mot de passe brut ne doit pas être modifié

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and utilisateur.check_password(password):
            session["utilisateur_id"] = utilisateur.id
            session["email"] = utilisateur.email
            session["prenom"] = utilisateur.nom_utilisateur

            flash("Connexion réussie !", "success")
            return redirect(url_for("compte_client"))
        else:
            flash("Adresse e-mail ou mot de passe incorrect.", "danger")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = escape(request.form.get("username"))
        email = escape(request.form.get("email"))
        password = request.form.get("password")

        # Vérifie si l'utilisateur existe déjà
        existing_user = Utilisateur.query.filter(
            (Utilisateur.email == email) | (Utilisateur.nom_utilisateur == username)
        ).first()

        if existing_user:
            flash(
                "Ce nom d'utilisateur ou cette adresse email est déjà utilisé(e).",
                "danger",
            )
            return redirect(url_for("signup"))

        # Création du compte
        user = Utilisateur(nom_utilisateur=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["utilisateur_id"] = user.id
        session["email"] = user.email
        session["prenom"] = username

        return redirect(url_for("formulaire_client"))

    return render_template("signup.html")


@app.route("/compte-client")
def compte_client():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour accéder à votre compte client.", "warning")
        return redirect(url_for("login"))

    devis_data = session.get("devis_data")  # données stockées temporairement
    clients = Client.query.filter_by(utilisateur_id=utilisateur_id).all()
    devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()

    return render_template(
        "compte_client.html",
        clients=clients,
        devis_data=devis_data,
        devis_list=devis_list,
    )


@app.route("/newsletter", methods=["POST"])
def newsletter():
    email = request.form.get("email")
    # Ajoutez ici la logique de traitement, par exemple enregistrer l'email dans un fichier ou envoyer un email de confirmation
    return "Merci de vous être inscrit(e) à notre newsletter !"


@app.route("/atelier")
def atelier():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "warning")
        return redirect(url_for("login"))
    return render_template("atelier.html")


@app.route("/nos-outils")
def nos_outils():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "warning")
        return redirect(url_for("login"))
    return render_template("nos_outils.html")


@app.route("/aide")
def aide():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "warning")
        return redirect(url_for("login"))

    return render_template("aide.html")


@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour accéder à vos paramètres.", "warning")
        return redirect(url_for("login"))

    # On récupère les informations stockées en session
    user = {
        "prenom": session.get("prenom", ""),
        "nom": session.get("nom", ""),
        "email": session.get("email", ""),
    }

    return render_template("parametres.html", user=user)


@app.route("/supprimer-devis", methods=["POST"])
def supprimer_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté pour gérer vos devis.", "warning")
        return redirect(url_for("login"))

    devis_id = request.form.get("devis_ids")

    # Vérification de l'ID
    if not devis_id or not devis_id.isdigit():
        flash("Identifiant de devis invalide ou manquant.", "danger")
        return redirect(url_for("parametres"))

    # Recherche sécurisée
    devis = Devis.query.filter_by(
        id=int(devis_id), utilisateur_id=utilisateur_id
    ).first()
    if devis:
        try:
            db.session.delete(devis)
            db.session.commit()
            flash("Le devis a été supprimé avec succès.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Une erreur est survenue lors de la suppression du devis.", "danger")
    else:
        flash("Ce devis n'existe pas ou ne vous appartient pas.", "danger")

    return redirect(url_for("parametres"))


@app.route("/update-password", methods=["GET", "POST"])
def update_password():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté pour modifier votre mot de passe.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Vérifie que les champs ne sont pas vides
        if not current_password or not new_password or not confirm_password:
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(url_for("update_password"))

        # Vérifie que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("update_password"))

        # Récupère l'utilisateur depuis la base
        utilisateur = Utilisateur.query.get(utilisateur_id)
        if not utilisateur or not utilisateur.check_password(current_password):
            flash("Le mot de passe actuel est incorrect.", "danger")
            return redirect(url_for("update_password"))

        # Met à jour le mot de passe
        utilisateur.set_password(new_password)
        db.session.commit()

        flash("Votre mot de passe a été mis à jour avec succès.", "success")
        return redirect(url_for("compte_client"))

    return render_template("update_password.html")


@app.route("/parametres/gerer-devis", methods=["GET", "POST"])
def gerer_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour accéder à vos devis.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        devis_ids = request.form.getlist("devis_ids")
        if devis_ids:
            devis_supprimes = 0
            for devis_id in devis_ids:
                try:
                    devis = Devis.query.get(int(devis_id))
                    if devis and devis.utilisateur_id == utilisateur_id:
                        db.session.delete(devis)
                        devis_supprimes += 1
                except ValueError:
                    continue  # Ignore les IDs invalides
            db.session.commit()
            if devis_supprimes:
                flash(f"{devis_supprimes} devis supprimé(s) avec succès.", "success")
            else:
                flash("Aucun devis valide à supprimer.", "info")
            return redirect(url_for("gerer_devis"))

    # GET : afficher les devis de l'utilisateur
    devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("gerer_devis.html", devis_list=devis_list)


@app.route("/update-profile", methods=["GET", "POST"])
def update_profile():
    if "utilisateur_id" not in session:
        flash("Vous devez être connecté pour modifier votre profil.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Sécurisation des champs avec escape()
        prenom = escape(request.form.get("prenom", ""))
        nom = escape(request.form.get("nom", ""))
        email = escape(request.form.get("email", ""))

        # Mise à jour dans la session (ou base de données si nécessaire)
        session["prenom"] = prenom
        session["nom"] = nom
        session["email"] = email

        flash("Vos informations ont été mises à jour.", "success")
        return redirect(url_for("compte_client"))

    # Pré-remplir le formulaire avec les infos sécurisées en session
    user = {
        "prenom": escape(session.get("prenom", "")),
        "nom": escape(session.get("nom", "")),
        "email": escape(session.get("email", "")),
    }
    return render_template("update_profile.html", user=user)


@app.route("/update-social", methods=["GET", "POST"])
def update_social():
    if "utilisateur_id" not in session:
        flash("Vous devez être connecté pour modifier vos réseaux sociaux.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Sécurisation des données avec escape()
        facebook = escape(request.form.get("facebook", ""))
        linkedin = escape(request.form.get("linkedin", ""))
        instagram = escape(request.form.get("instagram", ""))

        session["social"] = {
            "facebook": facebook,
            "linkedin": linkedin,
            "instagram": instagram,
        }

        flash("Vos réseaux sociaux ont été mis à jour.", "success")
        return redirect(url_for("parametres"))

    return render_template("update_social.html")


@app.route("/update_preferences", methods=["POST"])
def update_preferences():
    if "utilisateur_id" not in session:
        flash("Vous devez être connecté pour modifier vos préférences.", "warning")
        return redirect(url_for("login"))

    # Sécurisation des champs du formulaire
    language = escape(request.form.get("language", "fr"))
    theme = escape(request.form.get("theme", "light"))

    # Stockage en session
    session["language"] = language
    session["theme"] = theme

    flash("Préférences mises à jour avec succès.", "success")
    return redirect(url_for("account_settings"))  # Or 'parameters'


@app.route("/update_notifications", methods=["POST"])
def update_notifications():
    if "utilisateur_id" not in session:
        flash("Vous devez être connecté pour modifier vos notifications.", "warning")
        return redirect(url_for("login"))

    # Validation sécurisée des checkbox
    notif_email = "notif_email" in request.form
    notif_sms = "notif_sms" in request.form

    # Stockage en session ou à envoyer vers la BDD
    session["notifications"] = {"email": notif_email, "sms": notif_sms}

    flash("Vos préférences de notifications ont été mises à jour.", "success")
    return redirect(url_for("parametres"))


@app.route("/update_billing", methods=["POST"])
def update_billing():
    if "utilisateur_id" not in session:
        flash(
            "Vous devez être connecté pour modifier les informations de facturation.",
            "warning",
        )
        return redirect(url_for("login"))

    name = escape(request.form.get("billing_name", ""))
    address = escape(request.form.get("billing_address", ""))

    # Exemple : stockage en session (à adapter selon ton système)
    session["billing_info"] = {"name": name, "address": address}

    flash("Vos informations de facturation ont été mises à jour.", "success")
    return redirect(url_for("parametres"))


@app.before_request
def track_history():
    # Ne tracer que les requêtes GET
    if request.method != "GET":
        return

    # Ne pas enregistrer les ressources statiques, APIs, ou admin
    if request.path.startswith(("/static", "/admin", "/api", "/favicon.ico")):
        return

    # Ne pas enregistrer certaines pages sensibles
    IGNORED_PATHS = {"/login", "/logout", "/signup", "/update-password"}
    if request.path in IGNORED_PATHS:
        return

    # Initialiser la session 'history' si absente
    history = session.get("history", [])
    history.append(request.path)
    session["history"] = history[-20:]  # Garde les 20 dernières


@app.route("/historique")
def historique():
    history = session.get("history", [])
    if not history:
        flash("Aucune navigation enregistrée pour le moment.", "info")
    return render_template("historique.html", history=history)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/update_photo", methods=["POST"])
def update_photo():
    photo = request.files.get("photo")

    if not photo or photo.filename == "":
        flash("Aucune photo sélectionnée.", "danger")
        return redirect(url_for("parametres"))

    if not allowed_file(photo.filename):
        flash(
            "Format de fichier non autorisé. Formats acceptés : PNG, JPG, JPEG, GIF.",
            "danger",
        )
        return redirect(url_for("parametres"))

    filename = secure_filename(photo.filename)

    # Crée le dossier d'upload s'il n'existe pas
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Sauvegarde temporaire du fichier
    photo.save(filepath)

    # ✅ Vérification du contenu réel de l'image avec Pillow
    try:
        with Image.open(filepath) as img:
            img.verify()  # Vérifie que le fichier est bien une image
            img_format = img.format.lower()  # e.g. 'jpeg', 'png'
    except (UnidentifiedImageError, Exception):
        os.remove(filepath)
        flash("Le fichier n'est pas une image valide.", "danger")
        return redirect(url_for("parametres"))

    if img_format not in ALLOWED_EXTENSIONS:
        os.remove(filepath)
        flash("Le type de fichier image n'est pas autorisé.", "danger")
        return redirect(url_for("parametres"))

    # ✅ Enregistre le nom dans la session
    session["photo_url"] = filename
    flash("Votre photo de profil a bien été mise à jour.", "success")
    return redirect(url_for("parametres"))


@app.route("/grille-tarifaire")
def grille_tarifaire():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder à la grille tarifaire.", "warning")
        return redirect(url_for("login"))
    return render_template("grille_tarifaire.html")


@app.route("/ma-fiche-client")
def ma_fiche_client():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour voir votre fiche client.", "warning")
        return redirect(url_for("login"))

    utilisateur_id = session["utilisateur_id"]
    clients = Client.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("ma_fiche_client.html", clients=clients)


@app.route("/modifier-client/<int:client_id>", methods=["GET", "POST"])
def modifier_client(client_id):
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour modifier un client.", "warning")
        return redirect(url_for("login"))

    client = Client.query.get_or_404(client_id)

    # Vérifie que le client appartient à l'utilisateur connecté
    if client.utilisateur_id != session["utilisateur_id"]:
        flash("Accès non autorisé à ce client.", "danger")
        return redirect(url_for("ma_fiche_client"))

    if request.method == "POST":
        # Échapper tous les champs
        client.activite = escape(request.form.get("activite"))
        client.type_entreprise = escape(request.form.get("type_entreprise"))
        client.cabinet = escape(request.form.get("cabinet"))
        client.civilite = escape(request.form.get("civilite"))
        client.nom = escape(request.form.get("nom"))
        client.prenom = escape(request.form.get("prenom"))
        client.email = escape(request.form.get("email"))
        client.adresse_siege = escape(request.form.get("adresse_siege"))

        db.session.commit()
        flash("La fiche client a été mise à jour avec succès.", "success")
        return redirect(url_for("ma_fiche_client"))

    return render_template("modifier_client.html", client=client)


@app.route("/supprimer-client/<int:client_id>", methods=["POST"])
def supprimer_client(client_id):
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour effectuer cette action.", "warning")
        return redirect(url_for("login"))

    client = Client.query.get_or_404(client_id)

    # Vérifie que le client appartient à l'utilisateur connecté
    if client.utilisateur_id != session["utilisateur_id"]:
        flash("Accès interdit. Ce client ne vous appartient pas.", "danger")
        return redirect(url_for("ma_fiche_client"))

    db.session.delete(client)
    db.session.commit()
    flash("La fiche client a été supprimée avec succès.", "success")
    return redirect(url_for("ma_fiche_client"))


@app.route("/update_security", methods=["POST"])
def update_security():
    if "utilisateur_id" not in session:
        flash(
            "Vous devez être connecté pour modifier vos paramètres de sécurité.",
            "warning",
        )
        return redirect(url_for("login"))

    uses_2fa = request.form.get("2fa") == "on"
    session["uses_2fa"] = uses_2fa  # Enregistre l'état 2FA dans la session

    flash("Paramètres de sécurité mis à jour.", "success")
    return redirect(url_for("account_settings"))


@app.route("/export_data", methods=["POST"])
def export_data():
    if "utilisateur_id" not in session:
        flash("Vous devez être connecté pour exporter vos données.", "warning")
        return redirect(url_for("login"))

    data = {
        "prenom": session.get("prenom", "N/A"),
        "nom": session.get("nom", "N/A"),
        "email": session.get("email", "N/A"),
        "uses_2fa": session.get("uses_2fa", False),
    }

    response = jsonify(data)
    response.headers["Content-Disposition"] = "attachment; filename=mes_donnees.json"
    return response


@app.route("/contact_support", methods=["POST"])
def contact_support():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour contacter le support.", "warning")
        return redirect(url_for("login"))

    subject = escape(request.form.get("subject"))
    message = escape(request.form.get("message"))
    email = session.get("email", "non connecté")

    print("\n====== MESSAGE SUPPORT ======")
    print(f"Email : {email}")
    print(f"Objet : {subject}")
    print(f"Message : {message}")
    print("==============================\n")

    flash("Votre demande a bien été envoyée à notre équipe d'assistance.", "success")
    return redirect(url_for("account_settings"))


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour utiliser le chatbot.", "warning")
        return redirect(url_for("login"))

    latest_question = None
    latest_reponse = None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            question = escape(question)  # Protection XSS

            user_name = session.get("prenom", "Cher utilisateur")
            reponse = f"Merci {user_name}, nous avons bien reçu votre question et nous reviendrons vers vous rapidement."

            # Enregistrement dans MongoDB
            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})

            flash("Votre question a été envoyée avec succès !", "success")
            latest_question = question
            latest_reponse = reponse
            return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())
    history = messages

    return render_template(
        "chatbot.html",
        messages=messages,
        history=history,
        latest_question=latest_question,
        latest_reponse=latest_reponse,
    )


# ➡️ NOUVELLE route admin protégée (à ajouter)
@app.route("/admin-chatbot")
def admin_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))

    messages = list(
        mongo.db.chatbot.find().sort("_id", -1)
    )  # On trie pour afficher du plus récent au plus ancien
    return render_template("admin_chatbot.html", messages=messages)


# ✅ MODIFIER UNE RÉPONSE
@app.route("/modifier-reponse/<message_id>", methods=["POST"])
def modifier_reponse(message_id):
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    nouvelle_reponse = request.form.get("reponse", "").strip()

    if not nouvelle_reponse:
        flash("Erreur : la réponse ne peut pas être vide.", "danger")
        return redirect(url_for("admin_chatbot"))

    nouvelle_reponse = escape(nouvelle_reponse)

    try:
        mongo.db.chatbot.update_one(
            {"_id": ObjectId(message_id)}, {"$set": {"reponse": nouvelle_reponse}}
        )
        flash("Réponse modifiée avec succès ✅", "success")
    except Exception as e:
        flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")

    return redirect(url_for("admin_chatbot"))


@app.route("/logout-admin")
def logout_admin():
    session.pop("admin_logged_in", None)
    flash("Déconnecté avec succès ✅", "success")
    return redirect(url_for("login_admin"))


# ✅ SUPPRIMER UN MESSAGE
@app.route("/supprimer-message/<message_id>", methods=["POST"])
def supprimer_message(message_id):
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    try:
        result = mongo.db.chatbot.delete_one({"_id": ObjectId(message_id)})
        if result.deleted_count:
            flash("Message supprimé avec succès ✅", "success")
        else:
            flash("Message introuvable ou déjà supprimé ❌", "warning")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")

    return redirect(url_for("admin_chatbot"))


@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return redirect(url_for("login_admin"))

        # Recherche dans MongoDB
        admin = mongo.db.admin_users.find_one({"username": username})

        if admin and check_password_hash(admin.get("password", ""), password):
            session["admin_logged_in"] = True
            flash("Connexion réussie ✅", "success")
            return redirect(url_for("admin_chatbot"))
        else:
            flash("Identifiants invalides ❌", "danger")

    return render_template("login_admin.html")


@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))

    try:
        total_questions = mongo.db.chatbot.count_documents({})
        last_message = mongo.db.chatbot.find_one(sort=[("_id", -1)])
        last_question = last_message["question"] if last_message else None
    except Exception as e:
        flash(f"Erreur lors du chargement du tableau de bord : {e}", "danger")
        total_questions = 0
        last_question = None

    return render_template(
        "admin_dashboard.html",
        total_questions=total_questions,
        last_question=last_question,
    )


@app.route("/ajouter-message", methods=["GET", "POST"])
def ajouter_message():
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    if request.method == "POST":
        question = escape(request.form.get("question", "").strip())
        reponse = escape(request.form.get("reponse", "").strip())

        if question and reponse:
            try:
                mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
                flash("Message ajouté avec succès ✅", "success")
                return redirect(url_for("admin_chatbot"))
            except Exception as e:
                flash(f"Erreur : {str(e)}", "danger")
        else:
            flash("Tous les champs sont obligatoires ❌", "danger")

    return render_template("ajouter_message.html")


@app.route("/base-test")
def base_test():
    if not session.get("admin_logged_in"):
        flash("Accès refusé. Connexion requise.", "danger")
        return redirect(url_for("login_admin"))

    try:
        utilisateurs = Utilisateur.query.all()
    except Exception as e:
        flash(f"Erreur lors du chargement des utilisateurs : {e}", "danger")
        utilisateurs = []

    return render_template("base_test.html", utilisateurs=utilisateurs)


@app.route("/vider-historique", methods=["POST"])
def vider_historique():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Réservé aux administrateurs.", "danger")
        return redirect(url_for("login_admin"))

    try:
        mongo.db.chatbot.delete_many({})
        flash("L'historique a été vidé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")

    return redirect(url_for("chatbot"))


@app.route("/historique-chatbot")
def historique_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Réservé aux administrateurs.", "danger")
        return redirect(url_for("login_admin"))

    try:
        messages = mongo.db.chatbot.find().sort("_id", -1)
    except Exception as e:
        flash(f"Erreur lors du chargement de l'historique : {e}", "danger")
        messages = []

    return render_template("historique_chatbot.html", messages=messages)


@app.route("/changer-langue", methods=["POST"])
def changer_langue():
    langue = request.form.get("langue", "fr")
    if langue not in ["fr", "en"]:
        flash("Langue invalide.", "danger")
        return redirect(request.referrer or url_for("historique_chatbot"))

    session["langue"] = langue
    flash(f"Langue changée en : {langue.upper()}", "success")
    return redirect(request.referrer or url_for("historique_chatbot"))


@app.route("/securite")
def securite():
    if not session.get("utilisateur_id"):
        flash("Veuillez vous connecter pour accéder à cette page.", "warning")
        return redirect(url_for("login"))
    return render_template("securite.html")


@app.context_processor
def inject_current_year():
    try:
        return {"current_year": datetime.now().year}
    except Exception:
        return {"current_year": "N/A"}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"  # 🔐 Clé secrète indispensable

    with app.app_context():  # 🌐 Active le contexte Flask
        with app.test_client() as client:
            yield client


def test_admin_dashboard_requires_login(client):
    response = client.get("/admin-dashboard")
    if response.status_code != 302:
        raise AssertionError("Redirection attendue.")


def test_admin_dashboard_as_admin(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
    response = client.get("/admin-dashboard")
    assert b"Total des questions" in response.data  # adapts this text to the content


def test_base_test_displays_users(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
    response = client.get("/base-test")
    assert response.status_code == 200
    # Add checks according to the content of your database


def test_user_list_displays_users(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True

    # Adds a test user if none exists
    if not Utilisateur.query.filter_by(email="baptiste012chesneau@gmail.com").first():
        user = Utilisateur(
            nom_utilisateur="test1", email="baptiste012chesneau@gmail.com"
        )
        user.set_password("123456")
        db.session.add(user)
        db.session.commit()

    response = client.get("/base-test")
    assert b"test1" in response.data
    assert b"baptiste012chesneau@gmail.com" in response.data


@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.after_request
def add_cache_headers(response):
    if request.endpoint in [
        "blog",
        "notre_histoire",
        "notre_equipe",
        "rgpd",
        "mentions_legales",
    ]:
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


def test_admin_protected(client):
    response = client.get("/admin-dashboard")
    assert response.status_code == 302  # redirect to login


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
