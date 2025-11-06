from functools import wraps
from flask import request, jsonify
from db import SessionLocal
from models.employee import Employee

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session = SessionLocal()

        # TEMPORARY: Expecting user_id from headers
        user_id = request.headers.get("X-USER-ID")

        if not user_id:
            return jsonify({"error": "Missing X-USER-ID header"}), 401

        user = session.query(Employee).filter_by(id=user_id).first()

        if not user:
            return jsonify({"error": "Invalid user"}), 401

        if not user.is_admin:
            return jsonify({"error": "Forbidden: Admins only"}), 403

        return f(*args, **kwargs)
    return decorated
