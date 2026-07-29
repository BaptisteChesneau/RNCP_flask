from app import app, db, Utilisateur

with app.app_context():
    email_collab = "collaborateur@ml2c-conseil.com"

    # Vérifier si cet email existe déjà en BDD
    user_existant = Utilisateur.query.filter_by(email=email_collab).first()

    if user_existant:
        # Si le compte existe, on met à jour ses informations
        user_existant.prenom = "Sebastien"
        user_existant.nom = "Chesneau"
        user_existant.role = "collaborateur"
        db.session.commit()
        print(
            f"✅ Le profil de {user_existant.prenom} {user_existant.nom} a été mis à jour avec le rôle 'collaborateur' !"
        )
    else:
        # Création du nouveau collaborateur
        nouveau_collab = Utilisateur(
            email=email_collab,
            prenom="Sebastien",
            nom="Chesneau",
            role="collaborateur",
        )
        # Mot de passe temporaire à personnaliser
        nouveau_collab.set_password("ML2C_Sebastien2026!")

        db.session.add(nouveau_collab)
        db.session.commit()
        print(f"🎉 Collaborateur Sébastien Chesneau créé avec succès !")
        print(f"E-mail : {email_collab}")
        print(f"Mot de passe temporaire : ML2C_Sebastien2026!")