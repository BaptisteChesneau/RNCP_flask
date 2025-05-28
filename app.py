import os
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
from datetime import datetime
import pytest
from bs4 import BeautifulSoup

from datetime import timedelta
from wtforms import EmailField, StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet
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

# 🔐 Limiter configuration
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
# app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

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
    email_chiffre = db.Column(db.String(500), unique=True)  # ✅ Replaces "email"
    adresse_siege = db.Column(db.String(200))

    utilisateur = db.relationship("Utilisateur", back_populates="clients")

    def __repr__(self):
        return f"<Client {self.prenom} {self.nom}>"

# 🔐 Email property for transparent access (decryption)
    @property
    def email(self):
        try:
            return fernet.decrypt(self.email_chiffre.encode()).decode()
        except Exception:
            return "[erreur de déchiffrement]"

    @email.setter
    def email(self, value):
        self.email_chiffre = fernet.encrypt(value.encode()).decode()

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


# =================== MODÈLE HISTORIQUE (optionnel) ======================
class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), nullable=False
    )
    path = db.Column(db.String(200))  # URL/Visited path
    date_visite = db.Column(db.DateTime)  # Date/Time of the visit

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
    # Check that the user is logged in
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour consulter le résumé du devis.", "warning")
        return redirect(url_for("login"))

    # Limit the number of quotes per user (e.g., max 3)
    utilisateur_id = session.get("utilisateur_id")
    nombre_devis = Devis.query.filter_by(utilisateur_id=utilisateur_id).count()
    if nombre_devis >= 3:
        flash(
            "Vous avez déjà soumis le nombre maximum de devis autorisé (3).", "danger"
        )
        return redirect(url_for("compte_client"))

    # Retrieve form fields
    secteur = request.form.get("secteur")
    nom = request.form.get("nom")
    type_service = request.form.get("type_service")
    date_rdv = request.form.get("date_rdv")
    heure_rdv = request.form.get("heure_rdv")
    form_email = request.form.get("user_email")

    # Verify that the email matches
    client_email = session.get("email")
    if client_email and form_email != client_email:
        flash(
            "L'adresse e-mail renseignée ne correspond pas à celle de votre compte client.",
            "danger",
        )
        return redirect(url_for("devis"))

    # Save to the database
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

    # Send data to the summary page
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


@app.route("/paiement-stripe", methods=["GET", "POST"])
def paiement_stripe():
    if request.method == "POST":
        # Retrieve fields
        card_holder_name = request.form.get("card_holder_name")
        card_number = request.form.get("card_number")
        card_expiry = request.form.get("card_expiry")
        card_cvv = request.form.get("card_cvv")
        # ... Process / Validate / Call the Stripe API ...
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"Tentative de connexion avec : {email}")

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        print(f"Utilisateur trouvé : {utilisateur}")

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
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Créer l'utilisateur
        user = Utilisateur(nom_utilisateur=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Démarrer la session pour l'utilisateur
        session["utilisateur_id"] = user.id
        session["email"] = user.email
        session["prenom"] = username  # Pour le message de bienvenue

        # Rediriger vers le formulaire client
        return redirect(url_for("formulaire_client"))

    return render_template("signup.html")


@app.route("/compte-client")
def compte_client():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")  # données stockées temporairement

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


@app.route("/newsletter", methods=["POST"])
def newsletter():
    email = request.form.get("email")
    # Ajoutez ici la logique de traitement, par exemple enregistrer l'email dans un fichier ou envoyer un email de confirmation
    return "Merci de vous être inscrit(e) à notre newsletter !"


@app.route("/atelier")
def atelier():
    return render_template("atelier.html")


@app.route("/nos-outils")
def nos_outils():
    return render_template("nos_outils.html")


@app.route("/aide")
def aide():
    return render_template("aide.html")


@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    # Par exemple, récupérer les informations de l'utilisateur depuis la session ou une BDD
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
        # Ici, vous récupérez et traitez le formulaire pour mettre à jour le mot de passe
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Exemple de logique (à adapter à votre système d'authentification)
        if new_password != confirm_password:
            flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("update_password"))

        # Logique pour vérifier le mot de passe actuel et mettre à jour le nouveau mot de passe...
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

    # Récupère tous les devis liés à l'utilisateur
    devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("gerer_devis.html", devis_list=devis_list)


@app.route("/update-profile", methods=["GET", "POST"])
def update_profile():
    if request.method == "POST":
        # Récupérez les informations du formulaire
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

    return redirect(
        url_for("account_settings")
    )  # or 'parametres' or the exact route to your parameters page


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


@app.route("/update_security", methods=["POST"])
def update_security():
    uses_2fa = request.form.get("2fa") == "on"
    session["uses_2fa"] = uses_2fa  # Enregistre dans la session

    flash("Paramètres de sécurité mis à jour.", "success")
    return redirect(url_for("account_settings"))





@app.route("/export_data", methods=["POST"])
def export_data():
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
    subject = request.form.get("subject")
    message = request.form.get("message")
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
    latest_question = None
    latest_reponse = None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            from markupsafe import escape

            question = escape(question)

            # ✅ Réponse automatique personnalisable
            # Exemple : si tu veux ajouter le prénom de l'utilisateur ou une réponse différente
            user_name = session.get(
                "prenom", "Cher utilisateur"
            )  # Si tu stockes 'prenom' en session
            reponse = f"Merci {user_name}, nous avons bien reçu votre question et nous reviendrons vers vous rapidement."

            # ✅ Enregistrement dans MongoDB
            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
            flash("Votre question a été envoyée avec succès !", "success")
            latest_question = question
            latest_reponse = reponse
            return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())
    history = messages  # réutilise

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

    messages = list(mongo.db.chatbot.find())
    return render_template("admin_chatbot.html", messages=messages)


# ✅ MODIFIER UNE RÉPONSE
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


# ✅ SUPPRIMER UN MESSAGE
@app.route("/supprimer-message/<message_id>", methods=["POST"])
def supprimer_message(message_id):
    if not session.get("admin_logged_in"):
        flash("Accès interdit.", "danger")
        return redirect(url_for("login_admin"))

    mongo.db.chatbot.delete_one({"_id": ObjectId(message_id)})
    flash("Message supprimé avec succès !", "success")
    return redirect(url_for("admin_chatbot"))

@limiter.limit("5 per minute")  # max 5 tentatives par minute
@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Recherche de l'utilisateur admin en base MongoDB
        admin = mongo.db.admin_users.find_one({"username": username})

        # ✅ Sécurité renforcée : message unique si utilisateur inconnu ou mot de passe invalide
        if not admin or not check_password_hash(admin["password"], password):
            flash("Identifiants invalides ❌", "danger")
            return redirect(url_for("login_admin"))

        # Si tout est bon :
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
    last_message = mongo.db.chatbot.find_one(sort=[("_id", -1)])  # Le plus récent
    last_question = last_message["question"] if last_message else None

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
    response = client.get("/admin-user-table")  # route réelle à adapter
    assert response.status_code == 302  # redirection vers login


def test_admin_user_table_as_admin(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True
    response = client.get("/admin-user-table")
    assert b"User Database (Admin Only)" in response.data


def test_user_list_displays_users(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True

    # Ajouter un utilisateur factice si nécessaire via la DB
    response = client.get("/admin-user-table")
    assert b"test1" in response.data
    assert b"baptiste012chesneau@gmail.com" in response.data

@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"               # ❌ empêche le site d'être intégré dans une iframe
    response.headers["X-Content-Type-Options"] = "nosniff"     # 🔐 empêche l'interprétation erronée du contenu MIME
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"  # 🔎 empêche l'exposition d'URL complètes
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"  # 🛡️ limite les API HTML5
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
