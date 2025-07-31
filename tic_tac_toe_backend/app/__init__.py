from flask import Flask
from flask_cors import CORS
from .routes.health import blp as health_blp
from flask_smorest import Api
from flask_session import Session
import os

from app.models import db

def get_database_uri():
    # Use env variable provided in .env via container: SQLITE_DB
    sqlite_db = os.environ.get('SQLITE_DB', 'app.db')
    if not os.path.isabs(sqlite_db):
        sqlite_db = os.path.join(os.path.dirname(__file__), "../../", sqlite_db)
    return f"sqlite:///{sqlite_db}"

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})
app.config["API_TITLE"] = "My Flask API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = os.environ.get("SECRET_KEY", "tictactoesecret")

db.init_app(app)
Session(app)

api = Api(app)
api.register_blueprint(health_blp)

# Register game REST API
from .routes.game_api import blp as game_blp
api.register_blueprint(game_blp)

