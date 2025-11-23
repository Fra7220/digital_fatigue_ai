from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import db, Log

log_bp = Blueprint("log_bp", __name__)

# Save log
@log_bp.route("/add", methods=["POST"])
@jwt_required()
def add_log():
    user_id = get_jwt_identity()
    action = request.json.get("action")

    if not action:
        return jsonify({"error": "Action required"}), 400

    log_entry = Log(user_id=user_id, action=action)
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({"message": "Log added"}), 201


# Fetch logs
@log_bp.route("/", methods=["GET"])
@jwt_required()
def fetch_logs():
    user_id = get_jwt_identity()
    logs = Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc()).all()

    output = [{
        "id": log.id,
        "action": log.action,
        "timestamp": log.timestamp
    } for log in logs]

    return jsonify(output), 200

