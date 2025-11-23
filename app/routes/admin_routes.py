from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import db, User, Prediction, Log
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint("admin_bp", __name__)


# Admin-only decorator

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.is_deleted or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# Overview stats + Trends

@admin_bp.route("/overview", methods=["GET"])
@jwt_required()
@admin_required
def overview():
    period = request.args.get("period", "daily")
    start_param = request.args.get("start")
    end_param = request.args.get("end")
    now = datetime.utcnow()

    if start_param and end_param:
        try:
            start = datetime.fromisoformat(start_param)
            end = datetime.fromisoformat(end_param)
        except ValueError:
            return jsonify({"error":"Invalid date format"}),400
    else:
        end = now
        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return jsonify({"error": "Invalid period, use daily/weekly/monthly"}), 400

    total_users = User.query.filter(User.created_at >= start, User.is_deleted==False).count()
    total_predictions = Prediction.query.filter(Prediction.timestamp >= start).count()
    total_logs = Log.query.filter(Log.timestamp >= start).count()
    deleted_accounts = User.query.filter(User.is_deleted==True, User.created_at >= start).count()

    # User Growth Trend
    user_trend = {"labels": [], "values": []}
    prediction_trend = {"labels": [], "Low": [], "Moderate": [], "High": [], "Very High": []}

    delta = end - start
    for i in range(delta.days + 1):
        day = start + timedelta(days=i)
        next_day = day + timedelta(days=1)
        user_count = User.query.filter(User.created_at >= day, User.created_at < next_day, User.is_deleted==False).count()
        user_trend["labels"].append(day.strftime("%Y-%m-%d"))
        user_trend["values"].append(user_count)

        preds = Prediction.query.filter(Prediction.timestamp >= day, Prediction.timestamp < next_day).all()
        counts = {"Low":0,"Moderate":0,"High":0,"Very High":0}
        for p in preds:
            counts[p.predicted_label] = counts.get(p.predicted_label,0) + 1
        prediction_trend["labels"].append(day.strftime("%Y-%m-%d"))
        for key in counts:
            prediction_trend[key].append(counts[key])

    return jsonify({
        "period": period,
        "total_users": total_users,
        "deleted_accounts": deleted_accounts,
        "total_predictions": total_predictions,
        "total_logs": total_logs,
        "user_trend": user_trend,
        "prediction_trend": prediction_trend
    }), 200


# Users Table

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def user_stats():
    users = User.query.all()
    users_list = []
    for u in users:
        users_list.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "created_at": u.created_at.isoformat(),
            "is_deleted": u.is_deleted
        })
    return jsonify(users_list), 200


# Delete/Restore User

@admin_bp.route("/user/<int:user_id>/delete", methods=["POST"])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = True
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

@admin_bp.route("/user/<int:user_id>/restore", methods=["POST"])
@jwt_required()
@admin_required
def restore_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = False
    db.session.commit()
    return jsonify({"message": "User restored"}), 200


# Predictions Table

@admin_bp.route("/predictions", methods=["GET"])
@jwt_required()
@admin_required
def prediction_stats():
    period = request.args.get("period", "daily")
    start_param = request.args.get("start")
    end_param = request.args.get("end")
    now = datetime.utcnow()
    end = now

    if start_param and end_param:
        try:
            start = datetime.fromisoformat(start_param)
            end = datetime.fromisoformat(end_param)
        except ValueError:
            return jsonify({"error":"Invalid date format"}),400
    else:
        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return jsonify({"error": "Invalid period"}), 400

    query = Prediction.query.filter(Prediction.timestamp >= start, Prediction.timestamp <= end)
    predictions_list = {}
    for p in query.all():
        predictions_list.setdefault(p.predicted_label, []).append({
            "age": p.age,
            "screen_time": p.screen_time,
            "family_history": p.family_history,
            "predicted_label": p.predicted_label,
            "timestamp": p.timestamp.isoformat()
        })
    return jsonify({"period": period, "prediction_counts": predictions_list}), 200

