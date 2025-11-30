from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import init_db, SessionLocal, User
from recommender import Recommender
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import random
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SGMail

app = Flask(__name__)
app.secret_key = "dev-secret"

# ---------------- DATABASE INIT ----------------
init_db()
db = SessionLocal()
recommender = Recommender()
DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")

# ---------------- MAIN ROUTES ----------------
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

# ---------------- PROFILE PAGE ----------------
@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user = db.query(User).filter(User.id == session.get("user_id")).first()
    return render_template("profile.html", user=user)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check existing email
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        # Save new user
        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed)
        db.add(user)
        db.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
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

# ---------------- FORGOT PASSWORD + OTP ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = db.query(User).filter((User.username == email) | (User.email == email)).first()

        if not user:
            flash("No account found with this email / username", "error")
            return redirect(url_for("forgot_password"))

        otp = random.randint(100000, 999999)
        session["reset_email"] = email
        session["otp"] = otp

        message = SGMail(
            from_email="Tourist Recommender <syedaaaliya01@gmail.com>",
            to_emails=email,
            subject="Verify Your Identity - Tourist Recommender",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; background: #ffffff; border-radius: 10px;">
                <h2 style="color: #2c3e50; text-align: center;">Please verify your identity, {user.username}</h2>
                <p style="font-size: 16px; color: #555; text-align: center;">Here is your password reset verification code:</p>
                <div style="font-size: 40px; font-weight: bold; letter-spacing: 6px; text-align: center; margin: 20px 0; color: #2ecc71;">
                    {otp}
                </div>
                <p style="font-size: 14px; color: #888;">This code is valid for <strong>10 minutes</strong> and can only be used once.</p>
                <p style="font-size: 14px; color: #777;">If you didn’t request this, please ignore this email.</p>
                <br>
                <p style="font-size: 15px; color: #444;">Thank you,<br><strong>Tourist Recommender Team</strong></p>
            </div>
            """
        )

        try:
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            sg.send(message)
            flash("OTP has been sent to your email!", "success")
            return redirect(url_for("verify_otp"))
        except Exception as e:
            print(str(e))
            flash("Failed to send OTP. Please try again.", "error")

    return render_template("forgot_password.html")

# ---------------- OTP VERIFICATION ----------------
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp")

        if str(session.get("otp")) == entered_otp:
            return redirect(url_for("reset_password"))

        flash("Invalid OTP! Try again.", "error")

    return render_template("verify_otp.html")

# ---------------- RESET PASSWORD ----------------
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = session.get("reset_email")

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("reset_password"))

        user = db.query(User).filter(User.email == email).first()

        if not user:
            flash("User not found!", "error")
            return redirect(url_for("reset_password"))

        user.password = generate_password_hash(new_password)
        db.commit()

        flash("Password reset successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ---------------- API ROUTES ----------------
@app.route("/api/locations")
def api_locations():
    df = pd.read_csv(DATA_PATH, encoding="latin1")
    df = df.dropna(subset=["country", "state", "city"])
    data = {}
    for _, r in df.iterrows():
        data.setdefault(r["country"], {}).setdefault(r["state"], set()).add(r["city"])
    return jsonify({c: {s: list(ct) for s, ct in st.items()} for c, st in data.items()})

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.json or {}
    results = recommender.recommend(data, top_k=5)
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True)
