from markupsafe import escape
from bson.objectid import ObjectId
from extensions import mongo

def ajouter_question_chatbot(question, prenom_user):
    question_sanitisee = escape(question)
    reponse = f"Merci {prenom_user}, nous avons bien reçu votre question et nous reviendrons vers vous rapidement."
    mongo.db.chatbot.insert_one({"question": question_sanitisee, "reponse": reponse})
    return question_sanitisee, reponse

def modifier_reponse_chatbot(message_id, nouvelle_reponse):
    if nouvelle_reponse:
        mongo.db.chatbot.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"reponse": nouvelle_reponse}}
        )
        return True
    return False

def supprimer_message_chatbot(message_id):
    mongo.db.chatbot.delete_one({"_id": ObjectId(message_id)})