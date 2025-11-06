from functools import wraps
from flask import request, jsonify
from models.employee import Employee
import base64

def check_auth(username, password):
    """Check username and password"""
    user = Employee.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None

def authenticate():
    """Return 401 Unauthorized"""
    return jsonify({"message": "Authentication required"}), 401, {
        "WWW-Authenticate": 'Basic realm="Login Required"'
    }

def requires_auth():
    """Decorator for Basic Auth + optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Basic "):
                return authenticate()

            # Decode base64 credentials
            try:
                b64_credentials = auth_header.split(" ")[1]
                decoded = base64.b64decode(b64_credentials).decode("utf-8")
                username, password = decoded.split(":", 1)
            except Exception:
                return authenticate()

            user = check_auth(username, password)
            if not user:
                return authenticate()

            # Check admin status
            if not user.is_admin:
                return jsonify({"message": "Forbidden: insufficient permissions"}), 403

            # retrive user object to endpoint
            return f(user=user, *args, **kwargs)

        return decorated
    return decorator
