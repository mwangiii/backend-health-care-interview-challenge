import os
from flask import Flask
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache

load_dotenv()

# Initialize components
db = SQLAlchemy()
api = Api(
    prefix="/api",
    title="Tiberbu Healthcare Interview Challenge",
    version="1.0",
    description="API for managing healthcare data",
    doc="/api/docs",
)
migrate = Migrate()
jwt = JWTManager()
cache = Cache()


def create_app():
    """
    Create and configure the Flask application.

    This function initializes the Flask app, configures extensions such as
    SQLAlchemy, Flask-Migrate, JWTManager, and Flask-Caching, and registers
    API namespaces for patients, doctors, and appointments.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    from config import Config
    app.config.from_object(Config)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_TOKEN_LOCATION'] = ["headers"]
    app.config['JWT_HEADER_NAME'] = "Authorization"
    app.config['JWT_HEADER_TYPE'] = "Bearer"

    # Redis Cache configuration
    app.config['CACHE_TYPE'] = "redis"
    app.config['CACHE_REDIS_HOST'] = os.getenv("REDIS_HOST", "localhost")
    app.config['CACHE_REDIS_PORT'] = int(os.getenv("REDIS_PORT", 6379))
    app.config['CACHE_REDIS_DB'] = 0
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    # Initialize components
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    api.init_app(app)

    # Register API namespaces
    from app.patients.routes import patient_namespace
    api.add_namespace(patient_namespace, path="/patients")

    from app.doctors.routes import doctor_namespace
    api.add_namespace(doctor_namespace, path="/doctors")

    from app.appointments.routes import appointment_namespace
    api.add_namespace(appointment_namespace, path="/appointments")

    return app
