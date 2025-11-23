from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from app.models.models import db, User
from flask_jwt_extended import create_access_token
from authlib.integrations.flask_client import OAuth
import os

auth_bp = Blueprint("auth_bp", __name__)

# Initialize OAuth with the app context
oauth = OAuth(current_app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://www.googleapis.com/oauth2/v3/userinfo",
    client_kwargs={"scope": "openid email profile"},
)


# Signup (email + password)

@auth_bp.route("/register", methods=["POST"])
def signup():
    data = request.get_json()  # ensures JSON payload
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")

    if not full_name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    new_user = User(full_name=full_name, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    token = create_access_token(identity=str(new_user.id))  # ✅ Convert to string
    return jsonify({"message": "Signup successful", "token": token}), 201


# Login (email + password)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))  # ✅ Convert to string
    return jsonify({"message": "Login successful", "token": token}), 200


# Google OAuth login

@auth_bp.route("/google")
def google_login():
    redirect_uri = url_for("auth_bp.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route("/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("userinfo").json()

    google_id = user_info.get("sub")
    email = user_info.get("email")
    full_name = user_info.get("name")

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            full_name=full_name,
            email=email,
            google_id=google_id,
            password_hash="google_oauth"  # placeholder
        )
        db.session.add(user)
        db.session.commit()

    jwt_token = create_access_token(identity=str(user.id))  # ✅ Convert to string
    return jsonify({"message": "Google login successful", "token": jwt_token}), 200

