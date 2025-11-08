from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify

def requires_auth(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def requires_admin(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_jwt_identity()
        if not user.get("is_admin"):
            return jsonify({"error": "Admin only"}), 403
        return fn(*args, **kwargs)
    return wrapper
