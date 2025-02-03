from flask import Flask, render_template

app = Flask(__name__)

@app.route("/header")
def header():
    return render_template("header.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route ("/footer")
def footer():
    return render_template ("footer.html")

@app.route("/plateforme-client")
def plateforme_client():
    return render_template("plateforme_client.html")

if __name__ == "__main__":
    app.run(debug=True)