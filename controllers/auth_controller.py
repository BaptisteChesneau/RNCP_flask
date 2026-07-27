# controllers/auth_controller.py
from flask import session
from extensions import db  # 👈 Il faut ajouter db ici !
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
    return True

def valider_reset_password(token, password, confirm):
    return False, "Fonctionnalité indisponible."