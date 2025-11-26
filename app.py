# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import init_db, SessionLocal, User
from recommender import Recommender
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

# Initialize DB once (creates tables)
init_db()


# --- Helper: Get DB session per request ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


recommender = Recommender()


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    db = next(get_db())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        fullname = request.form.get("fullname")
        email = request.form.get("email")

        if not username or not password:
            flash("Enter username and password", "danger")
            return redirect(url_for("register"))

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, fullname=fullname, email=email)

        db.add(user)
        db.commit()

        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    db = next(get_db())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        user = db.query(User).filter(User.username == username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["username"] = user.username
        flash("Logged in successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        flash(f"Password reset link sent to {email}", "info")
        return redirect(url_for('login'))
    return render_template("forgot_password.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session.get("username"))


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json or {}

    context = {
        "type": data.get("type", "park"),
        "avg_cost": data.get("avg_cost", 10),
        "distance_km": data.get("distance_km", 2),
        "open_hour": data.get("open_hour", datetime.now().hour),
        "weather": data.get("weather", "sunny"),
        "travel_type": data.get("travel_type", "family"),
        "budget_level": data.get("budget_level", "low")
    }

    results = recommender.recommend(context, top_k=5)
    return jsonify({"results": results})


# ------------------------------
# Render / Production Server
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
