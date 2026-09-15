from extensions import db
from models.user import Utilisateur
from werkzeug.security import generate_password_hash

def generate_sql_explanation(query):
    q = query.upper()
    if "SELECT" in q:
        return "This is a SELECT query that retrieves data from a table. It may include WHERE, ORDER BY, JOIN clauses, etc."
    elif "INSERT" in q:
        return "This is an INSERT query used to add new data into a table."
    elif "UPDATE" in q:
        return "This is an UPDATE query used to modify existing data."
    elif "DELETE" in q:
        return "This is a DELETE query used to remove data from a table."
    elif "CREATE TABLE" in q:
        return "This creates a new table in the database."
    else:
        return "SQL query received, but the explanation is generic or unrecognized. Try SELECT, INSERT, etc."

def mettre_a_jour_utilisateur_admin(user_id, form_data):
    user = Utilisateur.query.get_or_404(user_id)
    user.nom_utilisateur = form_data.get("username")
    user.email = form_data.get("email")
    new_password = form_data.get("password")
    if new_password:
        user.mot_de_passe_hash = generate_password_hash(new_password)
    db.session.commit()

def supprimer_utilisateur_admin(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()