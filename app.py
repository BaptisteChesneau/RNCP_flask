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


@app.route("/mot-de-passe-oublie", methods=["GET", "POST"])
def mot_de_passe_oublie():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        demarrer_reinitialisation_mdp(email, app.config["MAIL_USERNAME"])
        flash(
            "Si un compte existe avec cette adresse, un e-mail de réinitialisation a été envoyé.",
            "success",
        )
        return redirect(url_for("mot_de_passe_oublie"))
    return render_template("mot_de_passe_oublie.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        success, message = valider_reset_password(
            token,
            request.form.get("password", "").strip(),
            request.form.get("confirm_password", "").strip(),
        )
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("login"))
    return render_template("reset_password.html", token=token)


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


@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    if "utilisateur_id" not in session:
        return redirect(url_for("login"))
    return render_template("parametres.html")


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


@app.route("/admin-chatbot")
def admin_chatbot():
    if not session.get("admin_logged_in"):
        flash("Accès interdit. Connecte-toi !", "danger")
        return redirect(url_for("login_admin"))
    messages = list(mongo.db.chatbot.find())
    return render_template("admin_chatbot.html", messages=messages)


# 🟢 ROUTE AJOUTÉE : Pour éviter les redirections brisées dans l'administration
@app.route("/admin-dashboard")
@app.route("/admin-utilisateurs")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    users = Utilisateur.query.all()
    return render_template("admin_dashboard.html", users=users)

@app.route("/admin-stats")
def admin_stats():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_stats.html")

@app.route("/admin-notifications")
def admin_notifications():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login_admin"))
    return render_template("admin_notifications.html")

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