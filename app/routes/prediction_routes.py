from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import db, Prediction
import joblib
import os
import pandas as pd
from datetime import datetime

prediction_bp = Blueprint("prediction_bp", __name__)

# Load trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "digital_fatigue_model.pkl")
model = joblib.load(MODEL_PATH)

# Risk label mapping
risk_mapping = {0: 'High', 1: 'Low', 2: 'Moderate', 3: 'Very High'}

@prediction_bp.route("/", methods=["POST"])
@jwt_required()
def predict():
    user_id = get_jwt_identity()  # JWT identity
    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        age = int(data.get("age"))
        screen_time = float(data.get("screen_time"))
        family_history = bool(data.get("family_history"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "Invalid input types. 'age' must be int, 'screen_time' float, 'family_history' boolean"
        }), 400

    if age < 0 or screen_time < 0:
        return jsonify({"error": "Age and screen time must be non-negative"}), 400

    try:
        # Prepare dataframe with correct columns
        df = pd.DataFrame([[age, screen_time, int(family_history)]],
                          columns=["Age", "Screen_Time", "Family_History"])
        # Predict numeric label
        pred_num = int(model.predict(df)[0])
        # Map numeric label to string
        pred_label = risk_mapping.get(pred_num, "Unknown")
    except Exception as e:
        return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

    # Save prediction to DB
    try:
        timestamp = datetime.utcnow()
        record = Prediction(
            user_id=user_id,
            age=age,
            screen_time=screen_time,
            family_history=family_history,
            predicted_label=pred_label,
            timestamp=timestamp
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save prediction: {str(e)}"}), 500

    return jsonify({
        "label": pred_label,
        "predicted_label": pred_label,
        "risk_numeric": pred_num,        # Numeric risk for charting
        "timestamp": timestamp.isoformat(),  # Prediction timestamp
        "message": "Prediction successful"
    }), 200

# Optional: user-specific history endpoint
@prediction_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    start = request.args.get("start")
    end = request.args.get("end")

    query = Prediction.query.filter_by(user_id=user_id)

    if start:
        query = query.filter(Prediction.timestamp >= pd.to_datetime(start))
    if end:
        query = query.filter(Prediction.timestamp <= pd.to_datetime(end))

    predictions = query.order_by(Prediction.timestamp.desc()).all()

    result = []
    for p in predictions:
        result.append({
            "age": p.age,
            "screen_time": p.screen_time,
            "family_history": p.family_history,
            "predicted_label": p.predicted_label,
            "timestamp": p.timestamp.isoformat()
        })

    return jsonify(result), 200

