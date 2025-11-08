from . import create_app
from flask_jwt_extended import JWTManager
from utils.token_blacklist import blacklist

app = create_app()
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
