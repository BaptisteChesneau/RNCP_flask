import os
from flask import Flask, render_template, request, redirect, url_for ,session, flash 
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()  # ✅ Charge les variables depuis .env
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'  # Clé secrète nécessaire pour la session

# Limiter la taille des fichiers (ex. : 2 Mo max)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# ================== CONFIG FLASK-MAIL ===================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Exemple : Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe'
# Pour un usage plus propre, vous pouvez aussi définir:
# app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

# Remplace par ton URL exacte Scalingo
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔵 Configuration MongoDB pour Flask-PyMongo
app.config["MONGO_URI"] = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")
mongo = PyMongo(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# =================== MODÈLES ======================
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
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

    # Relations avec les autres tables :
    devis = db.relationship("Devis", back_populates="utilisateur")
    paiements = db.relationship("Paiement", back_populates="utilisateur")
    support_tickets = db.relationship("SupportTicket", back_populates="utilisateur")
    preferences = db.relationship("Preferences", back_populates="utilisateur", uselist=False)
    historiques = db.relationship("Historique", back_populates="utilisateur")
    articles = db.relationship("BlogPost", back_populates="auteur")

    # Relation : un utilisateur peut avoir plusieurs clients
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
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    secteur = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    type_service = db.Column(db.String(100))
    date_rdv = db.Column(db.String(50))
    heure_rdv = db.Column(db.String(50))
    email = db.Column(db.String(120))

    # Relation : un Devis appartient à un Utilisateur
    utilisateur = db.relationship("Utilisateur", back_populates="devis")

    def __repr__(self):
        return f"<Devis {self.nom} - {self.type_service}>"

# =================== MODÈLE PAIEMENT (optionnel) ======================
class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    montant = db.Column(db.Float)  # Par ex. 49.99
    date_transaction = db.Column(db.DateTime)  # Nécessite éventuellement "from datetime import datetime"
    statut = db.Column(db.String(50))  # "validé", "en attente", "refusé", ...
    mode_paiement = db.Column(db.String(50))  # "Stripe", "PayPal", ...

    # Relation : un Paiement appartient à un Utilisateur
    utilisateur = db.relationship("Utilisateur", back_populates="paiements")

    def __repr__(self):
        return f"<Paiement #{self.id} - {self.statut}>"

# =================== MODÈLE NEWSLETTER (optionnel) ======================
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_inscription = db.Column(db.DateTime)  # Optionnel, si vous voulez enregistrer la date

    def __repr__(self):
        return f"<Newsletter {self.email}>"

# =================== MODÈLE SUPPORT TICKET (optionnel) ======================
class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    sujet = db.Column(db.String(200))
    message = db.Column(db.Text)
    date_creation = db.Column(db.DateTime)
    statut = db.Column(db.String(50))  # "nouveau", "en cours", "résolu", ...

    # Relation : un ticket peut appartenir à un utilisateur (ou pas, si anonyme)
    utilisateur = db.relationship("Utilisateur", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket #{self.id} - {self.sujet[:15]}...>"

# =================== MODÈLE PREFERENCES (optionnel) ======================
class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

    # Exemple de colonnes
    langue = db.Column(db.String(10))  # "FR", "EN", ...
    theme = db.Column(db.String(10))   # "light", "dark"...
    notif_email = db.Column(db.Boolean, default=True)
    notif_sms = db.Column(db.Boolean, default=False)

    # Relation : 1:1 avec Utilisateur (ou 1:N selon votre logique)
    utilisateur = db.relationship("Utilisateur", back_populates="preferences")

    def __repr__(self):
        return f"<Preferences #{self.id} - {self.utilisateur_id}>"

# =================== MODÈLE HISTORIQUE (optionnel) ======================
class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    path = db.Column(db.String(200))       # URL/Route visitée
    date_visite = db.Column(db.DateTime)   # Date/Heure de la visite

    # Relation : un historique appartient à un utilisateur
    utilisateur = db.relationship("Utilisateur", back_populates="historiques")

    def __repr__(self):
        return f"<Historique {self.path} - {self.date_visite}>"

# =================== MODÈLE BLOGPOST (optionnel) ======================
class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

    # Relation : un article de blog est écrit par un utilisateur
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
    print("DEBUG >>> utilisateur_id dans session :", utilisateur_id)  # 👈 à retirer plus tard
    if not utilisateur_id:
        flash("Vous devez être connecté pour remplir ce formulaire.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        # Récupération des données du formulaire
        activite = request.form.get("activite")
        type_entreprise = request.form.get("type_entreprise")
        cabinet = request.form.get("cabinet")
        civilite = request.form.get("civilite")
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        email = request.form.get("email")
        adresse_siege = request.form.get("adresse_siege")

        # ✅ Enregistrement dans la base de données avec lien à l'utilisateur
        nouveau_client = Client(
            utilisateur_id=utilisateur_id,
            activite=activite,
            type_entreprise=type_entreprise,
            cabinet=cabinet,
            civilite=civilite,
            nom=nom,
            prenom=prenom,
            email=email,
            adresse_siege=adresse_siege
        )
        db.session.add(nouveau_client)
        db.session.commit()

        # 📧 Envoi d'e-mail
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
            """
        )
        # mail.send(msg)  # ❌ à désactiver temporairement

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
    
    # Affiche le formulaire de prise de rendez-vous
    return render_template("devis.html")

MAX_DEVIS_PAR_UTILISATEUR = 1  # Nombre maximal de devis autorisés par utilisateur

@app.route("/resume-devis", methods=["POST"])
def resume_devis():
    # Vérifie que l'utilisateur est connecté
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour consulter le résumé du devis.", "warning")
        return redirect(url_for("login"))

    # Limiter le nombre de devis par utilisateur (ex: max 3)
    utilisateur_id = session.get("utilisateur_id")
    nombre_devis = Devis.query.filter_by(utilisateur_id=utilisateur_id).count()
    if nombre_devis >= 3:
        flash("Vous avez déjà soumis le nombre maximum de devis autorisé (3).", "danger")
        return redirect(url_for("compte_client"))

    # Récupère les champs du formulaire
    secteur = request.form.get("secteur")
    nom = request.form.get("nom")
    type_service = request.form.get("type_service")
    date_rdv = request.form.get("date_rdv")
    heure_rdv = request.form.get("heure_rdv")
    form_email = request.form.get("user_email")

    # Vérifier que l'e-mail correspond
    client_email = session.get("email")
    if client_email and form_email != client_email:
        flash("L'adresse e-mail renseignée ne correspond pas à celle de votre compte client.", "danger")
        return redirect(url_for("devis"))

    # Enregistrement dans la base de données
    nouveau_devis = Devis(
        utilisateur_id=utilisateur_id,
        secteur=secteur,
        nom=nom,
        type_service=type_service,
        date_rdv=date_rdv,
        heure_rdv=heure_rdv,
        email=form_email
    )
    db.session.add(nouveau_devis)
    db.session.commit()

    # Envoi des données à la page résumé
    return render_template("resume_devis.html",
                           secteur=secteur,
                           nom=nom,
                           type_service=type_service,
                           date_rdv=date_rdv,
                           heure_rdv=heure_rdv)

@app.route('/envoyer_mail')
def envoyer_mail():
    return "Fonction d'envoi par mail ici"

@app.route('/envoyer_compte')
def envoyer_compte():
    utilisateur_id = session.get("utilisateur_id")
    devis_data = session.get("devis_data")

    if not utilisateur_id or not devis_data:
        flash("Erreur : utilisateur non connecté ou données du devis manquantes.", "danger")
        return redirect(url_for("login"))

    # Vérifie si un devis identique a déjà été créé pour cet utilisateur
    devis_existant = Devis.query.filter_by(
        utilisateur_id=utilisateur_id,
        nom=devis_data.get("nom"),
        type_service=devis_data.get("type_service"),
        date_rdv=devis_data.get("date_rdv"),
        heure_rdv=devis_data.get("heure_rdv"),
        email=devis_data.get("email")
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
            email=devis_data.get("email")
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and utilisateur.check_password(password):
            # ✅ Stocker les infos en session
            session["utilisateur_id"] = utilisateur.id
            session["email"] = utilisateur.email
            session["prenom"] = utilisateur.nom_utilisateur  # Pour afficher le message "Bonjour X"
            
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

    return render_template("compte_client.html", 
                           clients=clients, 
                           devis_data=devis_data, 
                           devis_list=devis_list)

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
        "email": session.get("email", "")
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
        devis = Devis.query.filter_by(id=devis_id, utilisateur_id=utilisateur_id).first()
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
        # Mettez à jour les informations dans la base de données ou la session
        # update_user_profile(prenom, nom, email)
        # Par exemple, mettre à jour la session :
        session['prenom'] = prenom
        session['nom'] = nom
        session['email'] = email
        flash("Vos informations ont été mises à jour.", "success")
        return redirect(url_for("compte_client"))
    
    # Pour GET, on suppose que les informations de l'utilisateur sont stockées dans la session
    user = {
        "prenom": session.get("prenom", ""),
        "nom": session.get("nom", ""),
        "email": session.get("email", "")
    }
    return render_template("update_profile.html", user=user)

@app.route("/update-social", methods=["GET", "POST"])
def update_social():
    if request.method == "POST":
        facebook = request.form.get("facebook")
        linkedin = request.form.get("linkedin")
        instagram = request.form.get("instagram")
        # Vous pouvez enregistrer ces informations dans votre base de données
        # Ici, on les stocke dans la session pour l'exemple :
        session['social'] = {
            "facebook": facebook,
            "linkedin": linkedin,
            "instagram": instagram
        }
        flash("Vos réseaux sociaux ont été mis à jour.", "success")
        return redirect(url_for("parametres"))
    return render_template("update_social.html")

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    language = request.form.get('language')
    theme = request.form.get('theme')

    # Stocker les préférences dans la session
    session['language'] = language
    session['theme'] = theme

    flash("Préférences mises à jour avec succès.", "success")  # Ajout du message flash

    return redirect(url_for('account_settings'))  # ou 'parametres' ou la route exacte de ta page de paramètres

@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    notif_email = 'notif_email' in request.form
    notif_sms = 'notif_sms' in request.form
    print(f"Email: {notif_email}, SMS: {notif_sms}")
    return redirect(url_for('parametres'))

@app.route('/update_billing', methods=['POST'])
def update_billing():
    name = request.form.get('billing_name')
    address = request.form.get('billing_address')
    print(f"Facturation - Nom: {name}, Adresse: {address}")
    return redirect(url_for('parametres'))

@app.route("/historique")
def historique():
    # Récupérer l'historique de navigation depuis la session (ou une liste vide si inexistant)
    history = session.get("history", [])
    return render_template("historique.html", history=history)

@app.before_request
def track_history():
    if 'history' not in session:
        session['history'] = []
    # Ajoutez le chemin de la requête à l'historique
    session['history'].append(request.path)
    # Limiter l'historique aux 20 dernières entrées
    session['history'] = session['history'][-20:]

@app.route("/update_photo", methods=["POST"])
def update_photo():
    photo = request.files.get("photo")
    if photo:
        filename = secure_filename(photo.filename)
        upload_folder = os.path.join("static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        photo.save(filepath)
        session['photo_url'] = filename
        flash("Votre photo de profil a bien été mise à jour.", "success")
    else:
        flash("Aucune photo sélectionnée.", "danger")
    return redirect(url_for("parametres"))

@app.route('/grille-tarifaire')
def grille_tarifaire():
    return render_template('grille_tarifaire.html')

@app.route("/ma-fiche-client")
def ma_fiche_client():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour voir votre fiche client.", "warning")
        return redirect(url_for("login"))

    # Récupère tous les clients liés à ce user
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

@app.route('/update_security', methods=['POST'])
def update_security():
    uses_2fa = request.form.get('2fa') == 'on'
    session['uses_2fa'] = uses_2fa  # Enregistre dans la session

    flash("Paramètres de sécurité mis à jour.", "success")
    return redirect(url_for('account_settings'))

from flask import jsonify

@app.route('/export_data', methods=['POST'])
def export_data():
    data = {
        "prenom": session.get('prenom', 'N/A'),
        "nom": session.get('nom', 'N/A'),
        "email": session.get('email', 'N/A'),
        "uses_2fa": session.get('uses_2fa', False)
    }

    response = jsonify(data)
    response.headers["Content-Disposition"] = "attachment; filename=mes_donnees.json"
    return response

@app.route('/contact_support', methods=['POST'])
def contact_support():
    subject = request.form.get('subject')
    message = request.form.get('message')
    email = session.get('email', 'non connecté')

    print("\n====== MESSAGE SUPPORT ======")
    print(f"Email : {email}")
    print(f"Objet : {subject}")
    print(f"Message : {message}")
    print("==============================\n")

    flash("Votre demande a bien été envoyée à notre équipe d'assistance.", "success")
    return redirect(url_for('account_settings'))

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    latest_question = None
    latest_reponse = None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            # ✅ Protection minimale contre XSS : escape le contenu
            from markupsafe import escape
            question = escape(question)

            # ✅ Générer une réponse automatique
            reponse = "Merci pour votre question. Nous reviendrons vers vous prochainement."

            # ✅ Enregistrer la question et réponse générée dans MongoDB
            mongo.db.chatbot.insert_one({
                "question": question,
                "reponse": reponse
            })
            flash("Votre question a été envoyée avec succès !", "success")
            latest_question = question
            latest_reponse = reponse
            return redirect(url_for("chatbot"))

    # ✅ Charger une seule fois
    messages = list(mongo.db.chatbot.find())
    history = messages  # ➡️ Réutiliser

    return render_template(
        "chatbot.html",
        messages=messages,
        history=history,
        latest_question=latest_question,
        latest_reponse=latest_reponse
    )


@app.route("/vider-historique", methods=["POST"])
def vider_historique():
    mongo.db.chatbot.delete_many({})
    flash("L'historique a été vidé avec succès.", "success")
    return redirect(url_for("chatbot"))

@app.route("/historique-chatbot")
def historique_chatbot():
    messages = mongo.db.chatbot.find().sort("_id", -1)
    return render_template("historique_chatbot.html", messages=messages)

from flask import request, session

@app.route("/changer-langue", methods=["POST"])
def changer_langue():
    session['langue'] = request.form.get('langue', 'fr')
    return redirect(request.referrer or url_for('historique_chatbot'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
