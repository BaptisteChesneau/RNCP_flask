from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey_ml2c_conseil_2026")
app.config["MONGO_URI"] = os.getenv("MONGO_URL") or os.getenv("SCALINGO_MONGO_URL")
mongo = PyMongo(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

latest_question = None
latest_reponse = None


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    global latest_question, latest_reponse
    
    if request.method == "POST":
        question = request.form.get("question")
        
        reponse = f"Thank you for your question: '{question}'. An ML2C Conseil expert is reviewing your request."
        mongo.db.chatbot.insert_one({"question": question, "reponse": reponse})
        
        flash("Votre question a été envoyée avec succès !", "success")
        latest_question = question
        latest_reponse = reponse
        return redirect(url_for("chatbot"))

    messages = list(mongo.db.chatbot.find())
    history = messages  

    return render_template(
        "chatbot.html",
        messages=messages,
        history=history,
        latest_question=latest_question,
        latest_reponse=latest_reponse,
    )

@limiter.limit("5 per minute") 
@app.route("/login-admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = mongo.db.admin_users.find_one({"username": username})

        if not admin or not check_password_hash(admin["password"], password):
            flash("Identifiants invalides ❌", "danger")
            return redirect(url_for("login_admin"))

        session["admin_logged_in"] = True
        flash("Connexion réussie ✅", "success")
        return redirect(url_for("admin_chatbot"))

    return render_template("login_admin.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)