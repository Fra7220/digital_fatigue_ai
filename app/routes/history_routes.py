from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Prediction

history_bp = Blueprint("history_bp", __name__)

@history_bp.route("/", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()  # JWT identity as string

    try:
        records = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.timestamp.desc()).all()
        history = []
        for rec in records:
            history.append({
                "age": rec.age,
                "screen_time": rec.screen_time,
                "family_history": "Yes" if rec.family_history == 1 else "No",
                "predicted_label": rec.predicted_label,
                "timestamp": rec.timestamp.isoformat()
            })
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch history: {str(e)}"}), 500

