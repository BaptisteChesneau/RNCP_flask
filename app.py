from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message

app = Flask(__name__)

# ================== CONFIG FLASK-MAIL ===================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Exemple : Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe'
# Pour un usage plus propre, vous pouvez aussi définir:
# app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

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

        # Envoi d'e-mail
        msg = Message(
            subject="Nouvelle fiche client",
            sender=app.config["MAIL_USERNAME"],  # ou un autre expéditeur configuré
            recipients=["destinataire@example.com"],  # Mettez ici l'email qui doit recevoir la fiche
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
        mail.send(msg)

        # On pourrait aussi enregistrer en BDD, logger, etc.

        # Après traitement, on redirige vers la page de confirmation
        return redirect(url_for("confirmation"))

    # Si GET, on affiche simplement le formulaire
    return render_template("formulaire_client.html")

@app.route("/confirmation")
def confirmation():
    return "Formulaire soumis avec succès ! Merci."

@app.route("/devis", methods=["GET"])
def devis():
    # Affiche le formulaire de prise de rendez-vous
    return render_template("devis.html")

@app.route("/resume-devis", methods=["POST"])
def resume_devis():
    # Récupère les champs du formulaire
    secteur = request.form.get("secteur")
    nom = request.form.get("nom")
    type_service = request.form.get("type_service")
    date_rdv = request.form.get("date_rdv")
    heure_rdv = request.form.get("heure_rdv")

    # Ici vous pouvez : 
    # - Enregistrer en BDD
    # - Envoyer un email 
    # - Générer un PDF, etc.

    # On affiche la page de résumé en passant les valeurs
    return render_template("resume_devis.html",
                           secteur=secteur,
                           nom=nom,
                           type_service=type_service,
                           date_rdv=date_rdv,
                           heure_rdv=heure_rdv)

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

if __name__ == "__main__":
    app.run(debug=True)
