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

        # On stocke l'expéditeur
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
        # Côté Collaborateur : Récupère les messages échangés avec ce client
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
        # Côté Client : Récupère ses messages
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

    # 🔍 DISTINCTION VISUELLE EXACTE
    payload = []
    for m in messages:
        # Vérification si l'expéditeur est un Collaborateur
        collab_exp = Collaborateur.query.get(m.expediteur_id)
        is_expediteur_collab = collab_exp is not None

        if is_collab:
            # Pour la fenêtre d'un Collaborateur : "Moi" s'il est l'auteur
            is_me = m.expediteur_id == collab_id and is_expediteur_collab
            exp_label = "Moi (Support)" if is_me else "Client"
        else:
            # Pour la fenêtre d'un Client : "Moi" s'il est l'auteur (pas un collaborateur)
            is_me = (
                m.expediteur_id == utilisateur_id and not is_expediteur_collab
            )
            exp_label = "Moi" if is_me else "Support ML2C"

        payload.append(
            {
                "id": m.id,
                "contenu": m.contenu,
                "is_me": is_me,
                "expediteur": exp_label,
                "heure": (
                    m.date_creation.strftime("%H:%M") if m.date_creation else ""
                ),
            }
        )

    return jsonify(payload)