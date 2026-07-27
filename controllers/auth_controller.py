import secrets
from datetime import datetime, timedelta
from flask import session, flash, redirect, url_for, render_template
from flask_mail import Message
from extensions import db, mail
from models.user import Utilisateur

def traiter_login(email, password):
    user = Utilisateur.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session["utilisateur_id"] = user.id
        session["email"] = user.email
        session["prenom"] = user.nom_utilisateur
        return True
    return False

def traiter_signup(username, email, password, consent):
    if not username or not email or "@" not in email:
        return False, "Nom d'utilisateur ou e-mail invalide."
    if not password or len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not consent:
        return False, "Vous devez accepter les conditions."
    if Utilisateur.query.filter_by(email=email).first():
        return False, "Un compte existe déjà avec cette adresse e-mail."

    try:
        user = Utilisateur(nom_utilisateur=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session["utilisateur_id"] = user.id
        session["email"] = user.email
        session["prenom"] = username
        return True, "Compte créé avec succès !"
    except Exception:
        db.session.rollback()
        return False, "Une erreur est survenue lors de la création."

def demarrer_reinitialisation_mdp(email, mail_username):
    user = Utilisateur.query.filter_by(email=email).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        reset_url = url_for("reset_password", token=token, _external=True)
        msg = Message(
            subject="Réinitialisation de votre mot de passe - ML2C CONSEIL",
            sender=mail_username,
            recipients=[user.email],
            body=f"Bonjour {user.nom_utilisateur},\n\nCliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_url}\n\n— L'équipe ML2C CONSEIL"
        )
        try:
            mail.send(msg)
        except Exception:
            pass

def valider_reset_password(token, password, confirm):
    user = Utilisateur.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return False, "Ce lien est invalide ou a expiré."
    if not password or len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if password != confirm:
        return False, "Les mots de passe ne correspondent pas."

    user.set_password(password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    return True, "Mot de passe modifié avec succès !"