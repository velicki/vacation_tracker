import os
from flask_jwt_extended import JWTManager
from utils.token_blacklist import blacklist
from flask import Flask

from db import Base, engine
from routes.auth import auth_bp
from routes.users import users_bp
from routes.vacations import vacations_bp


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_envvar("APP_SETTINGS", silent=True)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")

    # Kreiranje tabela pomeramo van testova
    # Base.metadata.create_all(bind=engine)  <-- UKLANJAMO OVDЕ

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(vacations_bp, url_prefix="/vacations")

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in blacklist

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
