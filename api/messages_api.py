from flask import jsonify, request, session
from api import api_bp
from extensions import db
from models.collaborateur import Collaborateur
from models.message import MessageSupport
from models.user import Utilisateur


@api_bp.route("/messages", methods=["GET", "POST"])
def api_messages_passerelle():
    utilisateur_id = session.get("utilisateur_id") or session.get("user_id")
    collab_id = session.get("collaborateur_id")
    is_collab = session.get("is_collaborateur", False)

    if not utilisateur_id and not collab_id:
        return jsonify({"error": "Non autorisé"}), 403

    # ==========================================
    # 📤 ENVOI DE MESSAGE (POST)
    # ==========================================
    if request.method == "POST":
        data = request.get_json() or {}
        contenu = data.get("contenu", "").strip()
        destinataire_id = data.get("destinataire_id")

        if not contenu:
            return jsonify({"error": "Contenu vide"}), 400

        expediteur_id = (
            collab_id if (is_collab and collab_id) else utilisateur_id
        )

        nouveau_msg = MessageSupport(
            expediteur_id=expediteur_id,
            destinataire_id=destinataire_id if destinataire_id else None,
            contenu=contenu,
        )
        db.session.add(nouveau_msg)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message_id": nouveau_msg.id,
                    "heure": (
                        nouveau_msg.date_creation.strftime("%H:%M")
                        if nouveau_msg.date_creation
                        else ""
                    ),
                }
            ),
            201,
        )

    # ==========================================
    # 📥 RECEPTION / HISTORIQUE (GET)
    # ==========================================
    target_client_id = request.args.get("client_id", type=int)
    target_collab_id = request.args.get("collab_id", type=int)

    if is_collab and collab_id:
        if target_client_id:
            messages = (
                MessageSupport.query.filter(
                    (
                        (MessageSupport.expediteur_id == collab_id)
                        & (MessageSupport.destinataire_id == target_client_id)
                    )
                    | (
                        (MessageSupport.expediteur_id == target_client_id)
                        & (
                            (MessageSupport.destinataire_id == collab_id)
                            | (MessageSupport.destinataire_id.is_(None))
                        )
                    )
                )
                .order_by(MessageSupport.date_creation.asc())
                .all()
            )
        else:
            messages = (
                MessageSupport.query.filter(
                    (MessageSupport.expediteur_id == collab_id)
                    | (MessageSupport.destinataire_id == collab_id)
                )
                .order_by(MessageSupport.date_creation.asc())
                .all()
            )
    else:
        if target_collab_id:
            messages = (
                MessageSupport.query.filter(
                    (
                        (MessageSupport.expediteur_id == utilisateur_id)
                        & (MessageSupport.destinataire_id == target_collab_id)
                    )
                    | (
                        (MessageSupport.expediteur_id == target_collab_id)
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

    payload = []
    for m in messages:
        if is_collab:
            # Vue Collaborateur
            client_id_ref = (
                target_client_id
                if target_client_id
                else (
                    m.destinataire_id
                    if m.expediteur_id == collab_id
                    else m.expediteur_id
                )
            )

            if m.expediteur_id == client_id_ref:
                # C'est le client qui a parlé
                client_exp = Utilisateur.query.get(m.expediteur_id)
                exp_nom = (
                    f"{client_exp.prenom} {client_exp.nom}"
                    if client_exp
                    else "Client"
                )
                role_type = "client"
                is_me = False
            else:
                # C'est un collaborateur qui a parlé
                collab_exp = Collaborateur.query.get(m.expediteur_id)
                exp_nom = f"{collab_exp.prenom if collab_exp else 'Support'} (ML2C)"
                role_type = "collab"
                is_me = m.expediteur_id == collab_id
        else:
            # Vue Client
            if m.expediteur_id == utilisateur_id:
                # C'est le client connecté qui a parlé
                client_exp = Utilisateur.query.get(utilisateur_id)
                exp_nom = client_exp.prenom if client_exp else "Moi"
                role_type = "client"
                is_me = True
            else:
                # C'est le support qui a parlé
                collab_exp = Collaborateur.query.get(m.expediteur_id)
                exp_nom = (
                    f"{collab_exp.prenom} (ML2C)"
                    if collab_exp
                    else "Support ML2C"
                )
                role_type = "collab"
                is_me = False

        payload.append(
            {
                "id": m.id,
                "contenu": m.contenu,
                "is_me": is_me,
                "role": role_type,
                "expediteur": exp_nom,
                "heure": (
                    m.date_creation.strftime("%H:%M") if m.date_creation else ""
                ),
            }
        )

    return jsonify(payload)