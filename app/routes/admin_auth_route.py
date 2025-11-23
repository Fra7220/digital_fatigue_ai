from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.models import User

admin_auth_bp = Blueprint("admin_auth_bp", __name__)

@admin_auth_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    # Get admin user
    admin = User.query.filter_by(email=email, role="admin").first()

    if not admin:
        return jsonify({"message": "Admin not found"}), 404

    # Check password
    if not admin.check_password(password):
        return jsonify({"message": "Incorrect password"}), 401

    # Create token
    token = create_access_token(identity=str(admin.id), additional_claims={"role": "admin"})

    return jsonify({
        "message": "Admin login successful",
        "access_token": token
    }), 200

