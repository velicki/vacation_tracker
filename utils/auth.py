from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify
from functools import wraps

def requires_auth(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def requires_admin(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_jwt()
        if not user.get("is_admin"):
            return jsonify({"error": "Admin only"}), 403
        return fn(*args, **kwargs)
    return wrapper
