from flask import jsonify, request, session
from api import api_bp
from extensions import db
from models.message import MessageSupport


@api_bp.route("/messages", methods=["GET", "POST"])
def api_messages_passerelle():
    utilisateur_id = session.get("utilisateur_id") or session.get("user_id")
    collab_id = session.get("collaborateur_id")
    is_collab = session.get("is_collaborateur")

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

        # Identification de l'expéditeur selon le rôle
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
    # 📥 LECTURE HISTORIQUE MUTUEL (GET)
    # ==========================================
    target_client_id = request.args.get("client_id", type=int)
    target_collab_id = request.args.get("collab_id", type=int)

    # 🔹 CAS 1 : VUE COLLABORATEUR
    if is_collab and collab_id:
        if target_client_id:
            # Récupère tous les messages échangés entre le collaborateur connecté et ce client précis
            messages = (
                MessageSupport.query.filter(
                    (
                        (MessageSupport.expediteur_id == collab_id)
                        & (MessageSupport.destinataire_id == target_client_id)
                    )
                    | (
                        (MessageSupport.expediteur_id == target_client_id)
                        & (MessageSupport.destinataire_id == collab_id)
                    )
                )
                .order_by(MessageSupport.date_creation.asc())
                .all()
            )
        else:
            # Fil général du collaborateur
            messages = (
                MessageSupport.query.filter(
                    (MessageSupport.expediteur_id == collab_id)
                    | (MessageSupport.destinataire_id == collab_id)
                )
                .order_by(MessageSupport.date_creation.asc())
                .all()
            )

    # 🔹 CAS 2 : VUE CLIENT
    else:
        if target_collab_id:
            # Récupère tous les messages échangés entre le client et ce collaborateur précis
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
            # Tous les messages du client (Support Général + Collaborateurs)
            messages = (
                MessageSupport.query.filter(
                    (MessageSupport.expediteur_id == utilisateur_id)
                    | (MessageSupport.destinataire_id == utilisateur_id)
                )
                .order_by(MessageSupport.date_creation.asc())
                .all()
            )

    # Construction de la liste JSON
    payload = []
    for m in messages:
        is_me = (
            (m.expediteur_id == collab_id)
            if is_collab
            else (m.expediteur_id == utilisateur_id)
        )
        payload.append(
            {
                "id": m.id,
                "contenu": m.contenu,
                "is_me": is_me,
                "expediteur": (
                    "Moi"
                    if is_me
                    else (
                        m.expediteur.prenom or m.expediteur.email
                        if m.expediteur
                        else "Support ML2C"
                    )
                ),
                "heure": (
                    m.date_creation.strftime("%H:%M") if m.date_creation else ""
                ),
            }
        )

    return jsonify(payload)