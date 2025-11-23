import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from authlib.integrations.flask_client import OAuth

# Load environment variables
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

print("Loaded DATABASE_URL:", os.getenv("DATABASE_URL"))

# Frontend path
frontend_path = os.path.join(project_root, "frontend")

# Create Flask app
app = Flask(
    __name__,
    static_folder=frontend_path,
    static_url_path=''
)
app.url_map.strict_slashes = False

CORS(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devkey")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwtsecret")

# Import DB
from app.models.models import db
db.init_app(app)

# JWT
jwt = JWTManager(app)

# Google OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"access_type": "offline", "prompt": "consent"},
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://www.googleapis.com/oauth2/v3/userinfo",
    client_kwargs={"scope": "openid email profile"},
)



from app.routes.auth_routes import auth_bp
from app.routes.prediction_routes import prediction_bp
from app.routes.history_routes import history_bp
from app.routes.log_routes import log_bp
from app.routes.admin_routes import admin_bp
from app.routes.admin_auth_route import admin_auth_bp

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(prediction_bp, url_prefix="/api/predict")
app.register_blueprint(history_bp, url_prefix="/api/history")
app.register_blueprint(log_bp, url_prefix="/api/logs")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(admin_auth_bp, url_prefix="/api/auth/admin")

# Serve frontend
@app.route("/")
def index():
    return send_from_directory(frontend_path, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(frontend_path, path)

# Run
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Tables created successfully")

    app.run(host="0.0.0.0", port=5000, debug=True)

