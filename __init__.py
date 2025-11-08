import os
from flask import Flask
from db import engine, Base
from flask_jwt_extended import JWTManager
from utils.token_blacklist import blacklist

from .routes.auth import auth_bp
from .routes.users import users_bp
# from routes.vacations import vacations_bp

def create_app():
    app = Flask(__name__)
    app.config.from_envvar("APP_SETTINGS", silent=True)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    Base.metadata.create_all(bind=engine)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    # app.register_blueprint(vacations_bp, url_prefix="/vacations")

    JWTManager(app)

    return app
