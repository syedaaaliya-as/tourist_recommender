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

# Load locations for dropdowns
DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")

def load_locations():
    df = pd.read_csv(DATA_PATH, encoding="latin1", on_bad_lines="skip")
    df = df.dropna(subset=["country", "state", "city"])

    countries = {}
    for _, r in df.iterrows():
        c = str(r["country"]).strip()
        s = str(r["state"]).strip()
        city = str(r["city"]).strip()
        countries.setdefault(c, {}).setdefault(s, set()).add(city)

    return {c: {s: sorted(list(cities)) for s, cities in states.items()} for c, states in countries.items()}

@app.route("/api/locations", methods=["GET"])
def api_locations():
    try:
        df = pd.read_csv(DATA_PATH, encoding="latin1", on_bad_lines="skip")
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.dropna(subset=["country", "state", "city"])

        countries = {}
        for _, r in df.iterrows():
            c = r["country"].strip()
            s = r["state"].strip()
            city = r["city"].strip()
            countries.setdefault(c, {}).setdefault(s, set()).add(city)

        clean_data = {
            c: {s: sorted(list(cities)) for s, cities in states.items()}
            for c, states in countries.items()
        }

        return jsonify(clean_data)

    except Exception as e:
        print("❌ ERROR in /api/locations:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/ticket-info", methods=["POST"])
def ticket_info():
    data = request.json or {}
    mode = data.get("mode")
    distance = float(data.get("distance_km", 10))

    if not mode or mode not in TRAVEL_PRICING:
        return jsonify({"error": "Unknown travel mode"}), 400

    price = TRAVEL_PRICING[mode]["base_fare"] + TRAVEL_PRICING[mode]["per_km"] * distance

    return jsonify({"mode": mode, "distance_km": distance, "estimated_price": round(price, 2)})

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        fullname = request.form.get("fullname")
        email = request.form.get("email")

        if not username or not password:
            flash("Fill all fields", "danger")
            return redirect(url_for("register"))

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            flash("Username exists", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, fullname=fullname, email=email)
        db.add(user)
        db.commit()

        flash("Account created!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.query(User).filter(User.username == username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Wrong username / password", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["username"] = user.username
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    if not session.get("user_id"):
        return jsonify({"error": "Not logged in"}), 401

    data = request.json or {}

    context = {
        "country": data.get("country"),
        "state": data.get("state"),
        "city": data.get("city"),
        "type": data.get("type"),
        "avg_cost": float(data.get("avg_cost", 0)),
        "open_hour": data.get("open_hour", datetime.now().hour),
        "weather": data.get("weather"),
        "travel_type": data.get("travel_type"),
        "budget_level": data.get("budget_level"),
        "user_lat": data.get("user_lat"),
        "user_lng": data.get("user_lng"),
    }

    results = recommender.recommend(context, top_k=5)
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
