from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import init_db, SessionLocal, User
from recommender import Recommender
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "dev-secret"

init_db()
db = SessionLocal()
recommender = Recommender()

DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")

@app.route("/")
def index():
    return redirect(url_for("home"))

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed)
        db.add(user)
        db.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.query(User).filter(User.username == username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        flash("Invalid login", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/locations")
def api_locations():
    df = pd.read_csv(DATA_PATH, encoding="latin1")
    df = df.dropna(subset=["country", "state", "city"])
    data = {}
    for _, r in df.iterrows():
        data.setdefault(r["country"], {}).setdefault(r["state"], set()).add(r["city"])
    return jsonify({c: {s: list(cities) for s,cities in st.items()} for c,st in data.items()})

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.json or {}
    context = {k: data.get(k) for k in data}
    results = recommender.recommend(context, top_k=5)
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True)
