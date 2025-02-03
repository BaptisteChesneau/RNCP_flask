from flask import Flask, render_template

app = Flask(__name__)

@app.route("/menu")
def menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(debug=True)
