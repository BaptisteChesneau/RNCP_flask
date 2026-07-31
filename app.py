import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

# Configurations & Extensions
from config import Config
from extensions import db, mongo, migrate, mail, limiter

# ⚠️ OBLIGATOIRE : Charge tous les modèles pour que les relations SQLAlchemy (SupportTicket, etc.) fonctionnent
import models
from models.user import Utilisateur, ParametresCompte
from models.client import Client
from models.devis import Devis
from models.message import MessageSupport
from models.collaborateur import Collaborateur

# Mail reinitialisation
import resend
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# Messages en temps reel 
from api import api_bp


# Contrôleurs
from controllers.auth_controller import (
    traiter_login,
    traiter_signup,
    demarrer_reinitialisation_mdp,
    valider_reset_password,
)
from controllers.client_controller import (
    enregistrer_client,
    mettre_a_jour_client,
    supprimer_un_client,
)
from controllers.devis_controller import creer_devis, supprimer_devis_utilisateur
from controllers.admin_controller import (
    generate_sql_explanation,
    mettre_a_jour_utilisateur_admin,
    supprimer_utilisateur_admin,
)
from controllers.chatbot_controller import (
    ajouter_question_chatbot,
    modifier_reponse_chatbot,
    supprimer_message_chatbot,
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialisation des extensions
db.init_app(app)
mongo.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)
limiter.init_app(app)

# 🟢 CRÉATION AUTOMATIQUE DES TABLES EN BDD (PostgreSQL Scalingo)
with app.app_context():
    db.create_all()

# Enregistre toutes les routes API avec le préfixe /api
app.register_blueprint(api_bp, url_prefix="/api")

# ==================== MIDDLEWARES & HEADERS ====================


@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response


@app.before_request
def track_history():
    if "history" not in session:
        session["history"] = []
    session["history"].append(request.path)
    session["history"] = session["history"][-20:]


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login_admin"))
        return f(*args, **kwargs)

    return decorated_function


# ==================== NAVIGATION & PAGES STATIQUES ====================


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


@app.route("/notre-vision")
def notre_vision():
    return render_template("notre_vision.html")


@app.route("/nos-valeurs")
def nos_valeurs():
    return render_template("nos_valeurs.html")


@app.route("/nos-engagements")
def nos_engagements():
    return render_template("nos_engagements.html")


@app.route("/tenue-comptable")
def tenue_comptable():
    return render_template("tenue_comptable.html")


@app.route("/declarations-fiscales")
def declarations_fiscales():
    return render_template("declarations_fiscales.html")


@app.route("/pilotage-tableau-de-bord")
def pilotage_tableau_de_bord():
    return render_template("pilotage_tableau_de_bord.html")


@app.route("/paie-gestion")
def paie_gestion():
    return render_template("paie_gestion.html")


@app.route("/conseils-organisations")
def conseils_organisations():
    return render_template("conseils_organisations.html")


@app.route("/creation-reprise")
def creation_reprise():
    return render_template("creation_reprise.html")


@app.route("/juridique-courant")
def juridique_courant():
    return render_template("juridique_courant.html")


@app.route("/optimisation-digitalisation")
def optimisation_digitalisation():
    return render_template("optimisation_digitalisation.html")


@app.route("/assistance-support")
def assistance_support():
    return render_template("assistance_support.html")


@app.route("/actualites")
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


@app.route("/cookies")
def cookies():
    return render_template("cookies.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/grille-tarifaire")
def grille_tarifaire():
    return render_template("grille_tarifaire.html")


@app.route("/securite")
def securite():
    return render_template("securite.html")


@app.route("/nous-contacter")
def nous_contacter():
    return render_template("contact.html")

# --- CREATION COLLABORATEUR ---
@app.route("/creer-collaborateur", methods=["GET", "POST"])
def creer_collaborateur():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        collab = Collaborateur.query.filter_by(email=email).first()

        if collab:
            collab.set_password(password)
            db.session.commit()
            flash(
                f"Mot de passe mis à jour pour {email} ! ✅",
                "success",
            )
        else:
            nouveau_collab = Collaborateur(email=email, role="collaborateur")
            nouveau_collab.set_password(password)
            db.session.add(nouveau_collab)
            db.session.commit()
            flash(
                f"Compte collaborateur créé pour {email} ! 🎉",
                "success",
            )

        return redirect(url_for("collaborateur_login"))

    return render_template("creer_collaborateur.html")


# --- CONNEXION COLLABORATEUR ---
@app.route("/collaborateur-login", methods=["GET", "POST"])
def collaborateur_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        collab = Collaborateur.query.filter_by(email=email).first()

        if collab and collab.check_password(password):
            session["collaborateur_id"] = collab.id
            session["is_collaborateur"] = True
            session["email"] = collab.email
            flash(f"Bienvenue, {collab.email} ! 👋", "success")
            return redirect(url_for("collaborateur_dashboard"))
        else:
            flash("E-mail ou mot de passe incorrect.", "danger")

    return render_template("collaborateur_login.html")

# --- ROUTE DASHBOARD COLLABORATEUR ---
@app.route("/collaborateur-dashboard")
def collaborateur_dashboard():
    # Vérification que le collaborateur est bien connecté
    collab_id = session.get("collaborateur_id")
    if not collab_id:
        flash("Veuillez vous connecter à l'espace collaborateur.", "warning")
        return redirect(url_for("collaborateur_login"))

    # Récupération des données nécessaires
    collab = Collaborateur.query.get(collab_id)
    clients = Utilisateur.query.all()
    messages = (
        MessageSupport.query.order_by(MessageSupport.date_creation.desc())
        .limit(10)
        .all()
    )

    # Rendu vers ton nouveau template
    return render_template(
        "collaborateur_dashboard.html",
        user=collab,
        clients=clients,
        messages=messages,
    )

# --- SÉCURITÉ TOKENS & CONFIGURATION SMTP ---

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

def envoyer_email_reset(destinataire, reset_url):
    """Envoie un véritable e-mail de réinitialisation via l'API Resend."""
    resend.api_key = (app.config.get("RESEND_API_KEY") or os.getenv("RESEND_API_KEY", "")).strip()

    resend.Emails.send({
        "from": "onboarding@resend.dev",  # Adresse d'envoi fournie par défaut par Resend
        "to": destinataire,
        "subject": "Réinitialisation de votre mot de passe — ML2C CONSEIL",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #b81473; text-align: center;">ML2C CONSEIL</h2>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p>Bonjour,</p>
            <p>Vous avez demandé la réinitialisation de votre mot de passe pour votre compte ML2C CONSEIL.</p>
            <p>Veuillez cliquer sur le bouton ci-dessous pour choisir votre nouveau mot de passe (valide 30 minutes) :</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #b81473; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Réinitialiser mon mot de passe</a>
            </div>
            <p style="font-size: 0.85em; color: #666;">Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br><a href="{reset_url}">{reset_url}</a></p>
            <p style="font-size: 0.85em; color: #999;">Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail en toute sécurité.</p>
        </div>
        """
    })

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        # Validation du token (expire après 30 min)
        email = serializer.loads(
            token, salt="reset-password-salt", max_age=1800
        )
    except (SignatureExpired, BadTimeSignature):
        flash(
            "Le lien de réinitialisation est invalide ou a expiré ❌", "danger"
        )
        return redirect(url_for("mot_de_passe_oublie"))

    if request.method == "POST":
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        user = Utilisateur.query.filter_by(email=email).first()

        if not user:
            flash("Utilisateur introuvable.", "danger")
            return redirect(url_for("mot_de_passe_oublie"))

        # 1. Vérification de l'ancien mot de passe
        if not user.check_password(old_password):
            flash("L'ancien mot de passe est incorrect ❌", "danger")
            return render_template("reset_password.html", token=token)

        # 2. Vérification de la correspondance du nouveau mot de passe
        if new_password != confirm_password:
            flash(
                "Le nouveau mot de passe et sa confirmation ne correspondent pas.",
                "danger",
            )
            return render_template("reset_password.html", token=token)

        # 3. Mise à jour du mot de passe
        user.set_password(new_password)
        db.session.commit()
        flash("Votre mot de passe a été mis à jour avec succès ✅", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

@app.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = Utilisateur.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt="reset-password-salt")
            reset_url = url_for("reset_password", token=token, _external=True)

            try:
                envoyer_email_reset(email, reset_url)
                flash(
                    "Un e-mail de réinitialisation vous a été envoyé 📧",
                    "success",
                )
            except Exception as e:
                import traceback

                traceback.print_exc()  # Regarde tes logs Scalingo pour voir la cause exacte
                flash(
                    "Erreur lors de l'envoi. Vérifiez la clé API Resend.",
                    "danger",
                )
        else:
            flash(
                "Si un compte existe avec cette adresse, un e-mail a été envoyé.",
                "info",
            )

        return redirect(url_for("login"))

    return render_template("mot_de_passe_oublie.html")


@app.url_build_error_handlers.append
def handle_url_build_error(error, endpoint, values):
    if endpoint.startswith("admin_"):
        return f"#{endpoint}"
    raise error
# ==================== AUTHENTIFICATION ====================


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if traiter_login(email, password):
            flash("Connexion réussie !", "success")
            return redirect(url_for("compte_client"))
        else:
            flash("Email ou mot de passe invalide.", "danger")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message = traiter_signup(
            request.form.get("username", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("password", "").strip(),
            request.form.get("consent"),
        )
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("formulaire_client"))
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")

@app.route("/update-profile", methods=["POST"])
def update_profile():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté.", "warning")
        return redirect(url_for("login"))

    user = Utilisateur.query.get(utilisateur_id)
    if user:
        # Récupération du nom et prénom soumis
        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()

        # Si ton modèle regroupe nom et prénom dans nom_complet :
        if hasattr(user, "nom_complet"):
            user.nom_complet = f"{prenom} {nom}".strip()
        elif hasattr(user, "username"):
            user.username = request.form.get("username", user.username)

        # Email
        if hasattr(user, "email"):
            user.email = request.form.get("email", user.email).strip()

        db.session.commit()
        flash("Profil mis à jour avec succès ✅", "success")

    return redirect(url_for("parametres"))

@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour accéder aux paramètres.", "warning")
        return redirect(url_for("login"))

    user = Utilisateur.query.get(utilisateur_id)

    # TRAITEMENT DU FORMULAIRE (POST)
    if request.method == "POST":
        user.nom = request.form.get("nom", user.nom)
        user.prenom = request.form.get("prenom", user.prenom)
        user.email = request.form.get("email", user.email)
        db.session.commit()
        flash("Profil mis à jour avec succès !", "success")
        return redirect(url_for("parametres"))

    # AFFICHAGE DE LA PAGE (GET)
    return render_template("parametres.html", user=user)

@app.route("/update-password", methods=["POST"])
def update_password():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté.", "warning")
        return redirect(url_for("login"))

    user = Utilisateur.query.get(utilisateur_id)

    old_password = request.form.get("old_password", "").strip()
    new_password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    # 1. Vérification de l'ancien mot de passe
    if not user.check_password(old_password):
        flash("L'ancien mot de passe est incorrect ❌", "danger")
        return redirect(url_for("parametres"))

    # 2. Vérification de la correspondance
    if new_password != confirm_password:
        flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
        return redirect(url_for("parametres"))

    # 3. Mise à jour
    user.set_password(new_password)
    db.session.commit()
    flash("Mot de passe mis à jour avec succès ✅", "success")

    return redirect(url_for("parametres"))

@app.route("/update-notifications", methods=["POST"])
def update_notifications():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté.", "warning")
        return redirect(url_for("login"))

    # Logique pour sauvegarder les préférences si nécessaire
    flash("Préférences de notifications mises à jour ✅", "success")
    return redirect(url_for("parametres"))

@app.route("/supprimer-carte", methods=["POST"])
def supprimer_carte():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté.", "warning")
        return redirect(url_for("login"))

    # Logique pour supprimer la carte de l'utilisateur
    flash("Moyen de paiement supprimé avec succès ✅", "success")
    return redirect(url_for("parametres"))

@app.route("/supprimer-compte", methods=["POST"])
def supprimer_compte():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté.", "warning")
        return redirect(url_for("login"))

    user = Utilisateur.query.get(utilisateur_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash("Votre compte a été supprimé avec succès.", "info")

    return redirect(url_for("login"))

# ==================== FICHE CLIENT, PARAMÈTRES & DEVIS ====================


@app.route("/formulaire", methods=["GET", "POST"])
def formulaire_client():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté pour remplir ce formulaire.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        enregistrer_client(utilisateur_id, request.form)
        flash("Fiche client enregistrée avec succès ! ✅", "success")
        return redirect(url_for("compte_client"))

    return render_template("formulaire_client.html")


@app.route("/compte-client")
def compte_client():
    utilisateur_id = session.get("utilisateur_id")
    clients = (
        Client.query.filter_by(utilisateur_id=utilisateur_id).all()
        if utilisateur_id
        else []
    )
    devis_list = (
        Devis.query.filter_by(utilisateur_id=utilisateur_id).all()
        if utilisateur_id
        else []
    )
    return render_template("compte_client.html", clients=clients, devis_list=devis_list)


@app.route("/paiement")
def paiement():
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    return render_template("paiement.html")


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
    if request.method == "POST":
        mettre_a_jour_client(client_id, request.form)
        flash("La fiche client a été mise à jour avec succès.", "success")
        return redirect(url_for("ma_fiche_client"))
    client = Client.query.get_or_404(client_id)
    return render_template("modifier_client.html", client=client)


@app.route("/supprimer-client/<int:client_id>", methods=["POST"])
def supprimer_client(client_id):
    supprimer_un_client(client_id)
    flash("La fiche client a été supprimée.", "danger")
    return redirect(url_for("ma_fiche_client"))


@app.route("/devis")
def devis():
    if "utilisateur_id" not in session:
        flash("Veuillez vous connecter pour accéder au formulaire de devis.", "warning")
        return redirect(url_for("login"))
    return render_template("devis.html")


# 🟢 ROUTE AJOUTÉE : Nécessaire pour compte_client.html
@app.route("/gerer-devis")
def gerer_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour gérer vos devis.", "warning")
        return redirect(url_for("login"))
    devis_list = Devis.query.filter_by(utilisateur_id=utilisateur_id).all()
    return render_template("gerer_devis.html", devis_list=devis_list)


@app.route("/resume-devis", methods=["POST"])
def resume_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Veuillez vous connecter pour consulter le résumé du devis.", "warning")
        return redirect(url_for("login"))

    creer_devis(utilisateur_id, request.form)
    return render_template(
        "resume_devis.html",
        secteur=request.form.get("secteur"),
        nom=request.form.get("nom"),
        type_service=request.form.get("type_service"),
        date_rdv=request.form.get("date_rdv"),
        heure_rdv=request.form.get("heure_rdv"),
    )


@app.route("/supprimer-devis", methods=["POST"])
def supprimer_devis():
    utilisateur_id = session.get("utilisateur_id")
    if not utilisateur_id:
        flash("Vous devez être connecté pour gérer vos devis.", "warning")
        return redirect(url_for("login"))

    success, message = supprimer_devis_utilisateur(
        utilisateur_id, request.form.get("devis_ids")
    )
    flash(message, "success" if success else "danger")
    return redirect(url_for("parametres"))


# ==================== CHATBOT ====================


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    latest_question, latest_reponse = None, None
    if request.method == "POST":
        question = request.form.get("question")
        if question:
            prenom = session.get("prenom", "Cher utilisateur")
            latest_question, latest_reponse = ajouter_question_chatbot(question, prenom)
            flash("Votre question a été envoyée avec succès !", "success")
            return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())
    return render_template(
        "chatbot.html",
        messages=messages,
        history=messages,
        latest_question=latest_question,
        latest_reponse=latest_reponse,
    )


@app.route("/vider-historique", methods=["POST"])
def vider_historique():
    mongo.db.chatbot.delete_many({})
    flash("L'historique a été vidé avec succès.", "success")
    return redirect(url_for("chatbot"))


# ==================== ADMINISTRATION ====================


@limiter.limit("5 per minute")
@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        admin = mongo.db.admin_users.find_one(
            {"username": request.form.get("username")}
        )
        if admin and check_password_hash(
            admin["password"], request.form.get("password")
        ):
            session["admin_logged_in"] = True
            flash("Connexion réussie ✅", "success")
            return redirect(url_for("admin_chatbot"))
        flash("Identifiants invalides ❌", "danger")
    return render_template("login_admin.html")

# --- MESSAGERIE COLLABORATEUR ---
@app.route("/collaborateur-messagerie", methods=["GET", "POST"])
def collaborateur_messagerie():
    collab_id = session.get("collaborateur_id")

    # 1. Sécurité d'accès
    if not collab_id or not session.get("is_collaborateur"):
        flash("Veuillez vous connecter à l'espace collaborateur.", "warning")
        return redirect(url_for("collaborateur_login"))

    collab = Collaborateur.query.get(collab_id)
    clients = Utilisateur.query.all()

    # Client sélectionné
    client_id = request.args.get("client_id", type=int)
    client_selectionne = (
        Utilisateur.query.get(client_id) if client_id else None
    )

    # 2. Réception du message soumis par le formulaire (POST)
    if request.method == "POST":
        contenu = request.form.get("contenu", "").strip()
        dest_id = request.form.get("destinataire_id", type=int)

        if contenu and dest_id:
            nouveau_msg = MessageSupport(
                expediteur_id=collab.id,
                destinataire_id=dest_id,
                contenu=contenu,
            )
            db.session.add(nouveau_msg)
            db.session.commit()
            flash("Message envoyé au client ! ✅", "success")

            return redirect(
                url_for("collaborateur_messagerie", client_id=dest_id)
            )

    # 3. Chargement de l'historique
    messages = []
    if client_selectionne:
        messages = (
            MessageSupport.query.filter(
                (
                    (MessageSupport.expediteur_id == collab.id)
                    & (MessageSupport.destinataire_id == client_selectionne.id)
                )
                | (
                    (MessageSupport.expediteur_id == client_selectionne.id)
                    & (
                        (MessageSupport.destinataire_id == collab.id)
                        | (MessageSupport.destinataire_id.is_(None))
                    )
                )
            )
            .order_by(MessageSupport.date_creation.asc())
            .all()
        )

    return render_template(
        "collaborateur_messagerie.html",
        user=collab,
        clients=clients,
        client_selectionne=client_selectionne,
        messages=messages,
    )


# --- MESSAGERIE CLIENT (Strictement isolée) ---
@app.route("/messagerie", methods=["GET", "POST"])
def messagerie():
    utilisateur_id = session.get("utilisateur_id") or session.get("user_id")

    # Si ce n'est pas un client mais qu'un collaborateur est connecté, on autorise quand même l'accès ou on gère séparément
    if not utilisateur_id:
        if session.get("is_collaborateur"):
            return redirect(url_for("collaborateur_messagerie"))
        flash("Veuillez vous connecter à votre espace client.", "warning")
        return redirect(url_for("login"))

    user = Utilisateur.query.get(utilisateur_id)
    collaborateurs = Collaborateur.query.all()

    # Collaborateur sélectionné depuis l'URL (sidebar client)
    collab_id = request.args.get("collab_id", type=int)
    collab_selectionne = (
        Collaborateur.query.get(collab_id) if collab_id else None
    )

    if request.method == "POST":
        contenu = request.form.get("contenu", "").strip()
        destinataire_id = request.form.get("destinataire_id")

        if contenu:
            nouveau_msg = MessageSupport(
                expediteur_id=utilisateur_id,
                destinataire_id=destinataire_id if destinataire_id else None,
                contenu=contenu,
            )
            db.session.add(nouveau_msg)
            db.session.commit()
            flash("Message envoyé ! ✅", "success")

            if destinataire_id:
                return redirect(
                    url_for("messagerie", collab_id=destinataire_id)
                )
            return redirect(url_for("messagerie"))

    # Récupération des messages
    if collab_selectionne:
        messages = (
            MessageSupport.query.filter(
                (
                    (MessageSupport.expediteur_id == utilisateur_id)
                    & (MessageSupport.destinataire_id == collab_selectionne.id)
                )
                | (
                    (MessageSupport.expediteur_id == collab_selectionne.id)
                    & (MessageSupport.destinataire_id == utilisateur_id)
                )
            )
            .order_by(MessageSupport.date_creation.asc())
            .all()
        )
    else:
        messages = (
            MessageSupport.query.filter(
                (MessageSupport.expediteur_id == utilisateur_id)
                | (MessageSupport.destinataire_id == utilisateur_id)
            )
            .order_by(MessageSupport.date_creation.asc())
            .all()
        )

    return render_template(
        "messagerie.html",
        user=user,
        messages=messages,
        collaborateurs=collaborateurs,
        collab_selectionne=collab_selectionne,
    )

# --- DÉCLARATION DE TOUS LES TEMPLATES ADMINS ---


@app.route("/admin-chatbot")
def admin_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))
    messages = list(mongo.db.chatbot.find())
    return render_template("admin_chatbot.html", messages=messages)


@app.route("/admin-dashboard")
@app.route("/admin-utilisateurs")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    users = Utilisateur.query.all()
    return render_template("admin_dashboard.html", users=users)


admin_utilisateurs = admin_dashboard


@app.route("/admin-agenda")
def admin_agenda():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_agenda.html")


@app.route("/admin-audit")
def admin_audit():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_audit.html")


@app.route("/admin-blog")
def admin_blog():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_blog.html")


@app.route("/admin-blog-categories")
def admin_blog_categories():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_blog_categories.html")


@app.route("/admin-blog-new")
def admin_blog_new():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_blog_new.html")


@app.route("/admin-config")
def admin_config():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_config.html")


@app.route("/admin-emails")
def admin_emails():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_emails.html")


@app.route("/admin-export")
def admin_export():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_export.html")


@app.route("/admin-formulaires")
def admin_formulaires():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_formulaires.html")


@app.route("/admin-logs")
def admin_logs():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_logs.html")


@app.route("/admin-notifications")
def admin_notifications():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_notifications.html")


@app.route("/admin-parametres")
def admin_parametres():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_parametres.html")


@app.route("/admin-performances")
def admin_performances():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_performances.html")


@app.route("/admin-purge")
def admin_purge():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_purge.html")


@app.route("/admin-sauvegardes")
def admin_sauvegardes():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_sauvegardes.html")


@app.route("/admin-stats")
def admin_stats():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_stats.html")


@app.route("/admin-view-source")
def admin_view_source():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_view_source.html")

@app.route("/logout-admin")
def logout_admin():
    session.pop("admin_logged_in", None)
    flash("Déconnexion réussie 👋", "info")
    return redirect(url_for("login_admin"))

# --- ACTIONS ET MOTEUR ADMIN ---

@app.route("/modifier-reponse/<message_id>", methods=["POST"])
def modifier_reponse(message_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    if modifier_reponse_chatbot(message_id, request.form.get("reponse")):
        flash("Réponse modifiée avec succès !", "success")
    else:
        flash("Erreur : réponse vide.", "danger")
    return redirect(url_for("admin_chatbot"))


@app.route("/supprimer-message/<message_id>", methods=["POST"])
def supprimer_message(message_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    supprimer_message_chatbot(message_id)
    flash("Message supprimé avec succès !", "success")
    return redirect(url_for("admin_chatbot"))


@app.route("/explain-sql", methods=["GET", "POST"])
def explain_sql():
    query, explanation = "", ""
    if request.method == "POST":
        query = request.form.get("query", "")
        explanation = generate_sql_explanation(query)
    return render_template("explain_sql.html", query=query, explanation=explanation)


@app.route("/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    mettre_a_jour_utilisateur_admin(user_id, request.form)
    flash("Utilisateur mis à jour avec succès !", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/delete-user/<int:user_id>", methods=["POST"])
def supprimer_user(user_id):
    supprimer_utilisateur_admin(user_id)
    flash("Utilisateur supprimé avec succès !", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/ajouter-message", methods=["GET", "POST"])
def ajouter_message():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    if request.method == "POST":
        question = request.form.get("question")
        reponse = request.form.get("reponse")
        if question and reponse:
            mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
            flash("Nouvelle entrée ajoutée avec succès !", "success")
        else:
            flash("Veuillez remplir tous les champs.", "danger")
        return redirect(url_for("admin_chatbot"))
    return render_template("ajouter_message.html")


# ==================== ROUTES DE TEST D'ERREURS HTTP ====================


@app.route("/test-404")
def test_404():
    return render_template("404.html"), 404


@app.route("/test-500")
def test_500():
    return render_template("500.html"), 500


@app.route("/test-401")
def test_401():
    return render_template("401.html"), 401


@app.route("/test-403")
def test_403():
    return render_template("403.html"), 403


@app.route("/test-429")
def test_429():
    return render_template("429.html"), 429


@app.route("/test-503")
def test_503():
    return render_template("503.html"), 503


# ==================== GESTIONNAIRES D'ERREURS HTTP ====================


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(401)
def unauthorized(e):
    return render_template("401.html"), 401


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(429)
def too_many_requests(e):
    return render_template("429.html"), 429


@app.errorhandler(503)
def service_unavailable(e):
    return render_template("503.html"), 503


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)