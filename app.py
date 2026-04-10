import io
import base64
import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()  # ✅ Loads variables from .env
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import pytest
from bs4 import BeautifulSoup

from datetime import timedelta
from wtforms import EmailField, StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet
from functools import wraps

fernet = Fernet(os.environ.get("FERNET_KEY").encode())
from flask import jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

# 🔒 Secure configuration of session cookies
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = (
    True  # ❗ Enable this if you're using HTTPS (in production)
)
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# 🔐 Limit configuration
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],  # global rate limits per IP
)

# Good practice: show a message if the key is missing (optional but useful in dev)
if not app.secret_key:
    raise RuntimeError("APP_SECRET_KEY is not set in the environment.")

# Limit file size (e.g. 2 MB max)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# ================== CONFIG FLASK-MAIL ===================
app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Exemple : Gmail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "votre_email@gmail.com"
app.config["MAIL_PASSWORD"] = "votre_mot_de_passe"
# For a cleaner use, you can also define:
# app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

# Replace with your exact URL Scalingo
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 🔵 MongoDB configuration for Flask-PyMongo
app.config["MONGO_URI"] = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")
mongo = PyMongo(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


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
    email_chiffre = db.Column(db.String(500), unique=True)
    adresse_siege = db.Column(db.String(200))

    utilisateur = db.relationship("Utilisateur", back_populates="clients")

    # ✅ Relation via table de liaison
    utilisateurs_lies = db.relationship(
        "UtilisateurClient", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client {self.prenom} {self.nom}>"

    @property
    def email(self):
        try:
            return fernet.decrypt(self.email_chiffre.encode()).decode()
        except Exception:
            return "[erreur de déchiffrement]"

    @email.setter
    def email(self, value):
        self.email_chiffre = fernet.encrypt(value.encode()).decode()



class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"))
    utilisateur = db.relationship("Utilisateur", back_populates="historiques")


class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)

    # Relations avec d'autres tables
    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship("Preferences", back_populates="utilisateur", uselist=False)
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")
    parametres = db.relationship("ParametresCompte", back_populates="utilisateur", uselist=False)

    # ✅ Relations directes et via table de liaison
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
    statut = db.Column(db.String(50))  # "new", "in progress", "resolved", ...

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

    # Facturation ✅
    nom_facturation = db.Column(db.String(255))
    adresse_facturation = db.Column(db.String(255))

    # Date of update
    date_mise_a_jour = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    utilisateur = db.relationship(
        "Utilisateur", backref=db.backref("parametres_compte", uselist=False)
    )

    def __repr__(self):
        return f"<ParametresCompte utilisateur_id={self.utilisateur_id} langue={self.langue} theme={self.theme}>"


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

    # Relations
    utilisateur = db.relationship(
        "Utilisateur", back_populates="clients_lies", passive_deletes=True
    )
    client = db.relationship(
        "Client", back_populates="utilisateurs_lies", passive_deletes=True
    )


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


@app.route('/notre-vision')
def notre_vision():
    return render_template('notre_vision.html')

@app.route('/nos-valeurs')
def nos_valeurs():
    return render_template('nos_valeurs.html')

@app.route('/nos-engagements')
def nos_engagements():
    return render_template('nos_engagements.html')

@app.route('/tenue-comptable')
def tenue_comptable():
    return render_template('tenue_comptable.html')

@app.route('/declarations-fiscales')
def declarations_fiscales():
    return render_template('declarations_fiscales.html')

@app.route('/pilotage-tableau-de-bord')
def pilotage_tableau_de_bord():
    return render_template('pilotage_tableau_de_bord.html')

@app.route('/paie-gestion')
def paie_gestion():
    return render_template('paie_gestion.html')

@app.route('/conseils-organisations')
def conseils_organisations():
    return render_template('conseils_organisations.html')

@app.route('/creation-reprise')
def creation_reprise():
    return render_template('creation_reprise.html')

@app.route('/juridique-courant')
def juridique_courant():
    return render_template('juridique_courant.html')

@app.route('/optimisation-digitalisation')
def optimisation_digitalisation():
    return render_template('optimisation_digitalisation.html')

@app.route('/assistance-support')
def assistance_support():
    return render_template('assistance_support.html')

@app.route("/")
def index():
    return render_template("menu.html")


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
def formulaire_client():
    utilisateur_id = session.get("utilisateur_id")
    print(
        "DEBUG >>> utilisateur_id dans session :", utilisateur_id
    )  # 👈 to be removed later
    if not utilisateur_id:
        flash("Vous devez être connecté pour remplir ce formulaire.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Recovery of form data
        activite = request.form.get("activite")
        type_entreprise = request.form.get("type_entreprise")
        cabinet = request.form.get("cabinet")
        civilite = request.form.get("civilite")
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        adresse_siege = request.form.get("adresse_siege")

        # ✅ Database registration with link to user
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

        # 📧 Send e-mail
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
        # mail.send(msg) # ❌ to be temporarily disabled

        flash("Fiche client enregistrée avec succès ! ✅", "success")
        return redirect(url_for("compte_client"))

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

    # Récupération des champs
    secteur = request.form.get("secteur")
    nom = request.form.get("nom")
    type_service = request.form.get("type_service")
    date_rdv = request.form.get("date_rdv")
    heure_rdv = request.form.get("heure_rdv")
    form_email = request.form.get("user_email")

    # Sauvegarde en base
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

@app.route('/sauvegarder-devis', methods=['POST'])
def sauvegarder_devis():
    # Vérifier si ce devis existe déjà avant d'insérer
    existing = db.session.query(Devis).filter_by(
        email=request.form.get('user_email'),
        date_rdv=request.form.get('date_rdv'),
        heure_rdv=request.form.get('heure_rdv')
    ).first()
    if not existing:
        # insérer seulement si pas de doublon
        ...
    return redirect(url_for('compte_client'))

@app.route("/paiement")
def paiement():
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))
    return render_template('paiement.html')

@app.route("/envoyer_mail")
def envoyer_mail():
    flash("Cette fonctionnalité sera bientôt disponible. 🚀", "info")
    return redirect(url_for("menu"))


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

    # Check if an identical quote has already been created for this user
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
        # Create and save a new quote
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

@app.route('/actualites')
def blog():
    return render_template('blog.html')


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

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Récupération des données du formulaire
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"Tentative de connexion avec : {email}")

        # Rechercher l'utilisateur par email
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        print(f"Utilisateur trouvé : {utilisateur}")

        # Vérification du mot de passe
        if utilisateur and utilisateur.check_password(password):
            try:
                # Connexion normale
                session["utilisateur_id"] = utilisateur.id
                session["email"] = utilisateur.email
                session["prenom"] = utilisateur.nom_utilisateur

                print("Connexion réussie. Redirection vers /compte-client")
                flash("Connexion réussie !", "success")
                return redirect(url_for("compte_client"))

            except Exception as e:
                print("Erreur lors de l'enregistrement des données de session :", e)
                flash("Erreur interne lors de la connexion.", "danger")
                return redirect(url_for("login"))
        else:
            # Identifiants incorrects
            print("Email ou mot de passe invalide")
            flash("Email ou mot de passe invalide.", "danger")

    # Affichage de la page de connexion
    return render_template("login.html")

@app.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = Utilisateur.query.filter_by(email=email).first()

        # On répond toujours la même chose (sécurité anti-enumération)
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for("reset_password", token=token, _external=True)
            msg = Message(
                subject="Réinitialisation de votre mot de passe - ML2C CONSEIL",
                sender=app.config["MAIL_USERNAME"],
                recipients=[user.email],
                body=f"""Bonjour {user.nom_utilisateur},

Vous avez demandé à réinitialiser votre mot de passe.
Cliquez sur le lien suivant (valable 1 heure) :

{reset_url}

Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail.

— L'équipe ML2C CONSEIL
"""
            )
            try:
                mail.send(msg)
            except Exception:
                pass  # Ne pas révéler si l'envoi a échoué

        flash("Si un compte existe avec cette adresse, un e-mail de réinitialisation a été envoyé.", "success")
        return redirect(url_for("mot_de_passe_oublie"))

    return render_template("mot_de_passe_oublie.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = Utilisateur.query.filter_by(reset_token=token).first()

    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash("Ce lien est invalide ou a expiré.", "danger")
        return redirect(url_for("mot_de_passe_oublie"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()

        if not password or len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "danger")
            return render_template("reset_password.html", token=token)

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return render_template("reset_password.html", token=token)

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Mot de passe modifié avec succès ! Vous pouvez vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # ── Validations serveur ──
        if not username:
            flash("Le nom d'utilisateur est obligatoire.", "danger")
            return render_template("signup.html")

        if not email or "@" not in email:
            flash("Veuillez saisir une adresse e-mail valide.", "danger")
            return render_template("signup.html")

        if not password or len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "danger")
            return render_template("signup.html")

        if not request.form.get("consent"):
            flash("Vous devez accepter les conditions pour créer un compte.", "danger")
            return render_template("signup.html")

        # ── Email déjà utilisé ──
        if Utilisateur.query.filter_by(email=email).first():
            flash("Un compte existe déjà avec cette adresse e-mail.", "danger")
            return render_template("signup.html")

        # ── Création ──
        try:
            user = Utilisateur(nom_utilisateur=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Une erreur est survenue, veuillez réessayer.", "danger")
            return render_template("signup.html")

        session["utilisateur_id"] = user.id
        session["email"]          = user.email
        session["prenom"]         = username

        flash("Compte créé avec succès ! Bienvenue 🎉", "success")
        return redirect(url_for("formulaire_client"))

    return render_template("signup.html")

@app.route("/inscription", methods=["POST"])
def inscription():
    mot_de_passe = request.form.get("mot_de_passe", "")

    # Test du mot de passe faible (3 caractères dans le test)
    if len(mot_de_passe) < 6:
        return "mot de passe trop faible", 200

    return "inscription ok", 200


@app.route("/compte-client")
def compte_client():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")  # temporarily stored data

    clients = []
    devis_list = []

    if utilisateur_id:
        print("UTILISATEUR ID:", utilisateur_id)
        clients = Client.query.filter_by(utilisateur_id=utilisateur_id).all()
        devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()

    return render_template(
        "compte_client.html",
        clients=clients,
        devis_data=devis_data,
        devis_list=devis_list,
    )

@app.route("/compte")
def compte():
    return redirect(url_for("compte_client"))

@app.route("/newsletter", methods=["POST"])
def newsletter():
    email = request.form.get("email")
    # Add the processing logic here, for example, save the email to a file or send a confirmation email.
    return "Merci de vous être inscrit(e) à notre newsletter !"


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

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    # For example, retrieve user information from the session or a database.
    user = {
        "prenom": session.get("prenom", ""),
        "nom": session.get("nom", ""),
        "email": session.get("email", ""),
    }
    return render_template("parametres.html", user=user)

@app.route("/supprimer-compte", methods=["POST"])
def supprimer_compte():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        return redirect(url_for("login"))

    try:
        user = Utilisateur.query.get(utilisateur_id)
        if user:
            db.session.delete(user)
            db.session.commit()
        session.clear()
        flash("Votre compte a été supprimé définitivement.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Une erreur est survenue lors de la suppression.", "danger")
        return redirect(url_for("parametres"))

    return redirect(url_for("menu"))

@app.route("/supprimer-devis", methods=["POST"])
def supprimer_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté pour gérer vos devis.", "warning")
        return redirect(url_for("login"))

    devis_id = request.form.get("devis_ids")
    if devis_id:
        devis = Devis.query.filter_by(
            id=devis_id, utilisateur_id=utilisateur_id
        ).first()
        if devis:
            db.session.delete(devis)
            db.session.commit()
            flash("Le devis a été supprimé avec succès.", "success")
        else:
            flash("Ce devis n'existe pas ou ne vous appartient pas.", "danger")
    else:
        flash("Aucun devis sélectionné.", "warning")

    return redirect(url_for("parametres"))


@app.route("/update-password", methods=["GET", "POST"])
def update_password():
    if request.method == "POST":
        # Here, you retrieve and process the form to update the password.
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Example of logic (to be adapted to your authentication system)
        if new_password != confirm_password:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("update_password"))

        # Logic to verify the current password and update the new password...
        # update_user_password(current_password, new_password)
        flash("Votre mot de passe a été mis à jour.", "success")
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
            for devis_id in devis_ids:
                devis = Devis.query.get(int(devis_id))
                if devis and devis.utilisateur_id == utilisateur_id:
                    db.session.delete(devis)
            db.session.commit()
            flash("Les devis sélectionnés ont été supprimés avec succès.", "success")
            return redirect(url_for("gerer_devis"))

    # Retrieves all quotes related to the user
    devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("gerer_devis.html", devis_list=devis_list)


@app.route("/update-profile", methods=["GET", "POST"])
def update_profile():
    if request.method == "POST":
        # Retrieve information from the form
        prenom = request.form.get("prenom")
        nom = request.form.get("nom")
        email = request.form.get("email")
        # Update information in database or session
        # update_user_profile(firstname, lastname, email)
        # For example, update session :
        session["prenom"] = prenom
        session["nom"] = nom
        session["email"] = email
        flash("Vos informations ont été mises à jour.", "success")
        return redirect(url_for("compte_client"))

    # For GET, we assume that the user's information is stored in the session
    user = {
        "prenom": session.get("prenom", ""),
        "nom": session.get("nom", ""),
        "email": session.get("email", ""),
    }
    return render_template("update_profile.html", user=user)


@app.route("/update-social", methods=["GET", "POST"])
def update_social():
    if request.method == "POST":
        facebook = request.form.get("facebook")
        linkedin = request.form.get("linkedin")
        instagram = request.form.get("instagram")
        # You can save this information in your database
        # Here, we store them in the session for the example :
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
    language = request.form.get("language")
    theme = request.form.get("theme")

    # Store preferences in session
    session["language"] = language
    session["theme"] = theme

    flash("Préférences mises à jour avec succès.", "success")  # Add flash message

    return redirect(url_for("parametres"))# or 'parametres' or the exact route to your parameters page


@app.route("/update_notifications", methods=["POST"])
def update_notifications():
    notif_email = "notif_email" in request.form
    notif_sms = "notif_sms" in request.form
    print(f"Email: {notif_email}, SMS: {notif_sms}")
    return redirect(url_for("parametres"))


@app.route("/update_billing", methods=["POST"])
def update_billing():
    name = request.form.get("billing_name")
    address = request.form.get("billing_address")
    print(f"Facturation - Nom: {name}, Adresse: {address}")
    return redirect(url_for("parametres"))


@app.route("/historique")
def historique():
    # Recover browsing history from session (or an empty list if none exists)
    history = session.get("history", [])
    return render_template("historique.html", history=history)


@app.before_request
def track_history():
    if "history" not in session:
        session["history"] = []
    # Add query path to history
    session["history"].append(request.path)
    # Limit history to last 20 entries
    session["history"] = session["history"][-20:]


@app.route("/update_photo", methods=["POST"])
def update_photo():
    photo = request.files.get("photo")
    if photo:
        filename = secure_filename(photo.filename)
        upload_folder = os.path.join("static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        photo.save(filepath)
        session["photo_url"] = filename
        flash("Votre photo de profil a bien été mise à jour.", "success")
    else:
        flash("Aucune photo sélectionnée.", "danger")
    return redirect(url_for("parametres"))




@app.route("/supprimer-carte", methods=["POST"])
def supprimer_carte():
    session.pop("carte_bancaire", None)
    flash("Votre carte a été supprimée avec succès.", "success")
    return redirect(url_for("parametres"))


@app.route("/ajouter-carte-test", methods=["GET", "POST"])
def ajouter_carte_test():
    session["carte_bancaire"] = {
        "nom": "Jean Dupont",
        "numero": "4242424242424242",
        "expiration": "12/26",
    }
    return redirect(url_for("compte"))


@app.route("/grille-tarifaire")
def grille_tarifaire():
    return render_template("grille_tarifaire.html")


@app.route("/ma-fiche-client")
def ma_fiche_client():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour voir votre fiche client.", "warning")
        return redirect(url_for("login"))

    # Retrieves all clients linked to this user
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
        flash("La fiche client a été mise à jour avec succès.", "success")
        return redirect(url_for("ma_fiche_client"))

    return render_template("modifier_client.html", client=client)


@app.route("/supprimer-client/<int:client_id>", methods=["POST"])
def supprimer_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("La fiche client a été supprimée.", "danger")
    return redirect(url_for("ma_fiche_client"))


@app.route("/export_data", methods=["POST"])
def export_data():
    data = {
        "prenom": session.get("prenom", "N/A"),
        "nom": session.get("nom", "N/A"),
        "email": session.get("email", "N/A")
        # "uses_2fa" supprimé
    }

    response = jsonify(data)
    response.headers["Content-Disposition"] = "attachment; filename=mes_donnees.json"
    return response



@app.route("/contact_support", methods=["POST"])
def contact_support():
    subject = request.form.get("subject")
    message = request.form.get("message")
    email = session.get("email", "non connecté")

    print("\n====== MESSAGE SUPPORT ======")
    print(f"Email : {email}")
    print(f"Objet : {subject}")
    print(f"Message : {message}")
    print("==============================\n")

    flash("Votre demande a bien été envoyée à notre équipe d'assistance.", "success")
    return redirect(url_for("parametres"))


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    latest_question = None
    latest_reponse = None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            from markupsafe import escape

            question = escape(question)

            # ✅ Customizable automatic response
            # Example: if you want to add the user's first name or a different response
            user_name = session.get(
                "prenom", "Cher utilisateur"
            )  # If you store ‘first name’ in session
            reponse = f"Merci {user_name}, nous avons bien reçu votre question et nous reviendrons vers vous rapidement."

            # ✅ Recording in MongoDB
            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
            flash("Votre question a été envoyée avec succès !", "success")
            latest_question = question
            latest_reponse = reponse
            return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())
    history = messages  # reuse

    return render_template(
        "chatbot.html",
        messages=messages,
        history=history,
        latest_question=latest_question,
        latest_reponse=latest_reponse,
    )

@app.route('/admin/statistiques')
def admin_stats():
    return render_template('admin_stats.html')

@app.route('/admin/admin-configuration', endpoint='admin_config')
def admin_configuration():
    return render_template('admin_config.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login_admin"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/view-source')
@login_required
def admin_view_source():
    return render_template('admin_view_source.html')

@app.route('/admin/log-de-sécurite')
def admin_logs():
    return render_template('admin_logs.html')

@app.route('/admin/emails-automatiques')
def admin_emails():
    return render_template('admin_emails.html')

@app.route('/admin/export-des-donnees')
def admin_export():
    return render_template('admin_export.html')

@app.route('/admin/purger-les-logs')
def admin_purge():
    return render_template('admin_purge.html')

@app.route('/admin/parametres')
def admin_parametres(): return render_template('admin_parametres.html')

@app.route('/admin/utilisateurs')
def admin_utilisateurs(): return render_template('admin_utilisateurs.html')

@app.route('/admin/notifications')
def admin_notifications():
    return render_template('admin_notifications.html')

@app.route('/admin/agenda')
def admin_agenda():
    return render_template('admin_agenda.html')

@app.route('/admin/blog')
def admin_blog():
    return render_template('admin_blog.html')

@app.route('/admin/blog/nouveau')
def admin_blog_new():
    return render_template('admin_blog_new.html')

@app.route('/admin/blog/categories')
def admin_blog_categories():
    return render_template('admin_blog_categories.html')

@app.route('/admin/formulaires')
def admin_formulaires():
    return render_template('admin_formulaires.html')

@app.route('/admin/performances')
def admin_performances():
    return render_template('admin_performances.html')

@app.route('/admin/sauvegardes')
def admin_sauvegardes():
    return render_template('admin_sauvegardes.html')

@app.route('/admin/audit')
def admin_audit():
    return render_template('admin_audit.html')

# ➡️ NEW protected admin route (to be added)
@app.route("/admin-chatbot")
def admin_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))

    messages = list(mongo.db.chatbot.find())
    return render_template("admin_chatbot.html", messages=messages)


# ✅ EDIT AN ANSWER
@app.route("/modifier-reponse/<message_id>", methods=["POST"])
def modifier_reponse(message_id):
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    nouvelle_reponse = request.form.get("reponse")
    if nouvelle_reponse:
        mongo.db.chatbot.update_one(
            {"_id": ObjectId(message_id)}, {"$set": {"reponse": nouvelle_reponse}}
        )
        flash("Réponse modifiée avec succès !", "success")
    else:
        flash("Erreur : réponse vide.", "danger")

    return redirect(url_for("admin_chatbot"))


@app.route("/logout-admin")
def logout_admin():
    session.pop("admin_logged_in", None)
    flash("Déconnecté avec succès ✅", "success")
    return redirect(url_for("login_admin"))

@app.route('/logout')
def logout():
    session.clear()
    flash("Déconnecté avec succès ✅", "success")
    return redirect(url_for('menu'))

# ✅ DELETE A MESSAGE
@app.route("/supprimer-message/<message_id>", methods=["POST"])
def supprimer_message(message_id):
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    mongo.db.chatbot.delete_one({"_id": ObjectId(message_id)})
    flash("Message supprimé avec succès !", "success")
    return redirect(url_for("admin_chatbot"))


@limiter.limit("5 per minute")  # max 5 attempts per minute
@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Search for the admin user in the MongoDB database
        admin = mongo.db.admin_users.find_one({"username": username})

        # ✅ Enhanced security: unique message if user unknown or password invalid
        if not admin or not check_password_hash(admin["password"], password):
            flash("Identifiants invalides ❌", "danger")
            return redirect(url_for("login_admin"))

        # If everything is OK:
        session["admin_logged_in"] = True
        flash("Connexion réussie ✅", "success")
        return redirect(url_for("admin_chatbot"))

    return render_template("login_admin.html")


@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))

    total_questions = mongo.db.chatbot.count_documents({})
    last_message = mongo.db.chatbot.find_one(sort=[("_id", -1)])  # The most recent
    last_question = last_message["question"] if last_message else None

    return render_template(
        "admin_dashboard.html",
        total_questions=total_questions,
        last_question=last_question,
    )

@app.route('/test-404')
def test_404():
    return render_template('404.html'), 404

@app.route('/test-500')
def test_500():
    return render_template('500.html'), 500

@app.route('/test-401')
def test_401():
    return render_template('401.html'), 401

@app.route('/test-403')
def test_403():
    return render_template('403.html'), 403

@app.route('/test-429')
def test_429():
    return render_template('429.html'), 429

@app.route('/test-503')
def test_503():
    return render_template('503.html'), 503

@app.route("/ajouter-message", methods=["GET", "POST"])
def ajouter_message():
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    if request.method == "POST":
        question = request.form.get("question")
        reponse = request.form.get("reponse")

        if question and reponse:
            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
            flash("Message ajouté avec succès ✅", "success")
            return redirect(url_for("admin_chatbot"))
        else:
            flash("Tous les champs sont obligatoires ❌", "danger")

    return render_template("ajouter_message.html")


@app.route("/base-test")
def base_test():
    if not session.get("admin_logged_in"):
        flash("Access denied. Admin login required.", "danger")
        return redirect(url_for("login_admin"))

    utilisateurs = Utilisateur.query.all()
    return render_template("base_test.html", utilisateurs=utilisateurs)


@app.route("/edit/<int:user_id>")
def edit_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    return render_template("edit_user.html", user=user)


@app.route("/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    user.nom_utilisateur = request.form["username"]
    user.email = request.form["email"]

    new_password = request.form.get("password")
    if new_password:
        user.mot_de_passe_hash = generate_password_hash(new_password)

    db.session.commit()
    flash("User updated successfully!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/delete-user/<int:user_id>", methods=["POST"])
def supprimer_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/edit-inline")
def edit_inline():
    return render_template("edit_inline.html")  # to be created


@app.route("/save-inline-edits", methods=["POST"])
def save_inline_edits():
    # Here you can retrieve the POST data for processing:
    # username_1, email_1, active_1, etc.
    print("✅ Inline edits received:", dict(request.form))
    flash("Changes saved (simulation)", "success")
    return redirect(url_for("admin_view"))


@app.route("/edit")
def edit_page():
    return render_template("edit.html")  # to be created


@app.route("/explain-sql", methods=["GET", "POST"])
def explain_sql():
    query = ""
    explanation = ""
    if request.method == "POST":
        query = request.form.get("query", "")
        explanation = generate_sql_explanation(query)
    return render_template("explain_sql.html", query=query, explanation=explanation)


def generate_sql_explanation(query):
    q = query.upper()

    if "SELECT" in q:
        return "This is a SELECT query that retrieves data from a table. It may include WHERE, ORDER BY, JOIN clauses, etc."
    elif "INSERT" in q:
        return "This is an INSERT query used to add new data into a table."
    elif "UPDATE" in q:
        return "This is an UPDATE query used to modify existing data."
    elif "DELETE" in q:
        return "This is a DELETE query used to remove data from a table."
    elif "CREATE TABLE" in q:
        return "This creates a new table in the database."
    else:
        return "SQL query received, but the explanation is generic or unrecognized. Try SELECT, INSERT, etc."


@app.route("/view-php")
def view_php():
    return render_template("view_php.html")  # to be created


@app.route("/refresh")
def refresh_page():
    # Redirects to the same page or reloads the data
    return redirect(
        url_for("admin_view")
    )  # Replace ‘admin_view’ with the actual name of your admin view


@app.route("/vider-historique", methods=["POST"])
def vider_historique():
    mongo.db.chatbot.delete_many({})
    flash("L'historique a été vidé avec succès.", "success")
    return redirect(url_for("chatbot"))


@app.route("/historique-chatbot")
def historique_chatbot():
    messages = mongo.db.chatbot.find().sort("_id", -1)
    return render_template("historique_chatbot.html", messages=messages)


@app.route("/changer-langue", methods=["POST"])
def changer_langue():
    session["langue"] = request.form.get("langue", "fr")
    return redirect(request.referrer or url_for("historique_chatbot"))


@app.route("/securite")
def securite():
    return render_template("securite.html")


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_admin_user_table_requires_login(client):
    response = client.get("/admin-user-table")  # actual route to be adjusted
    assert response.status_code == 302  # redirect to login


def test_admin_user_table_as_admin(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
    response = client.get("/admin-user-table")
    assert b"User Database (Admin Only)" in response.data


def test_user_list_displays_users(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True

    # Add a dummy user if necessary via the DB
    response = client.get("/admin-user-table")
    assert b"test1" in response.data
    assert b"baptiste012chesneau@gmail.com" in response.data

@app.route("/admin-user-table")
def admin_user_table():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))

    utilisateurs = Utilisateur.query.all()
    return render_template("admin_user_table.html", utilisateurs=utilisateurs)

def test_user_model():
    user = Utilisateur(nom_utilisateur="test_user", email="test@ml2c.com")
    user.set_password("test123")
    db.session.add(user)
    db.session.commit()

    retrieved = Utilisateur.query.filter_by(nom_utilisateur="test_user").first()
    assert retrieved is not None, "Utilisateur non trouvé"
    assert retrieved.nom_utilisateur == "test_user"
    return "✅ test_user_model passé"


def test_client_model():
    user = Utilisateur.query.filter_by(nom_utilisateur="test_user").first()
    assert user is not None, "Utilisateur de test introuvable"

    client = Client(
        utilisateur_id=user.id, nom="Durand", prenom="Claire", type_entreprise="SARL"
    )
    client.email = "claire@example.com"
    db.session.add(client)
    db.session.commit()

    retrieved = Client.query.filter_by(nom="Durand").first()
    assert retrieved is not None, "Client non trouvé"
    assert retrieved.email == "claire@example.com"
    return "✅ test_client_model passé"


def test_utilisateur_client_relation():
    user = Utilisateur.query.filter_by(nom_utilisateur="test_user").first()
    client = Client.query.filter_by(nom="Durand").first()
    assert user and client, "Utilisateur ou Client manquant"

    liaison = UtilisateurClient(utilisateur_id=user.id, client_id=client.id)
    db.session.add(liaison)
    db.session.commit()

    found = UtilisateurClient.query.filter_by(
        utilisateur_id=user.id, client_id=client.id
    ).first()
    assert found is not None, "Liaison non créée"
    return "✅ test_utilisateur_client_relation passé"


def test_support_model():
    user = Utilisateur.query.filter_by(nom_utilisateur="test_user").first()
    assert user is not None, "Utilisateur manquant"

    ticket = SupportTicket(
        utilisateur_id=user.id, sujet="Test Sujet", message="Test message"
    )
    db.session.add(ticket)
    db.session.commit()

    retrieved = SupportTicket.query.filter_by(utilisateur_id=user.id).first()
    assert retrieved and retrieved.sujet == "Test Sujet"
    return "✅ test_support_model passé"


def test_devis_model():
    user = Utilisateur.query.filter_by(nom_utilisateur="test_user").first()
    assert user is not None, "Utilisateur manquant"

    devis = Devis(
        utilisateur_id=user.id,
        nom="Devis Test",
        type_service="Conseil",
        date_rdv=datetime.utcnow(),
    )
    db.session.add(devis)
    db.session.commit()

    retrieved = Devis.query.filter_by(nom="Devis Test").first()
    assert retrieved is not None
    assert retrieved.type_service == "Conseil"
    return "✅ test_devis_model passé"


def test_sql_injection(client):
    # Attempted SQL injection in the username field
    malicious_input = "' OR 1=1; --"
    response = client.post(
        "/login",
        data={"nom_utilisateur": malicious_input, "mot_de_passe": "fakepassword"},
        follow_redirects=True,
    )

    # Check that the application does not grant access and does not crash.
    assert response.status_code == 200
    assert (
        b"Identifiants invalides" in response.data
        or b"connexion" in response.data.lower()
    )


def test_weak_password_rejection(client):
    # Registration with a weak password
    response = client.post(
        "/inscription",
        data={
            "nom_utilisateur": "test_weak_pw",
            "email": "weak@test.com",
            "mot_de_passe": "123",  # too weak
            "confirmation": "123",
        },
        follow_redirects=True,
    )

    # The application must refuse registration.
    assert response.status_code == 200
    assert b"mot de passe trop faible" in response.data.lower()


def test_error_handling(client):
    response = client.get("/page-inexistante", follow_redirects=True)
    assert response.status_code == 404
    assert (
        "Page non trouvée".encode("utf-8") in response.data or b"404" in response.data
    )

    response_500 = client.get("/forcetest500", follow_redirects=True)
    assert response_500.status_code == 500
    assert "Une erreur s'est produite".encode("utf-8") in response_500.data
    assert b"Traceback" not in response_500.data


def validate_id(id_value, id_name="ID"):
    if not isinstance(id_value, int) or id_value <= 0:
        return f"{id_name} doit être un entier positif."
    return None


@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = (
        "DENY"  # ❌ prevents the site from being embedded in an iframe
    )
    response.headers["X-Content-Type-Options"] = (
        "nosniff"  # 🔐 prevents misinterpretation of MIME content
    )
    response.headers["Referrer-Policy"] = (
        "no-referrer-when-downgrade"  # 🔎 prevents the exposure of full URLs
    )
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=()"  # 🛡️ limits HTML5 APIs
    )
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(429)
def too_many_requests(e):
    return render_template('429.html'), 429

@app.errorhandler(503)
def service_unavailable(e):
    return render_template('503.html'), 503

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


