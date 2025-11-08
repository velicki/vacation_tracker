from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash, generate_password_hash

from db import SessionLocal
from models.employee import Employee
from utils.auth import requires_admin, requires_auth
from utils.token_blacklist import blacklist

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login", endpoint="login")
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    with SessionLocal() as session:
        user = session.query(Employee).filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(identity={"id": user.id, "is_admin": user.is_admin})
        return jsonify({"access_token": token})

@auth_bp.post("/register", endpoint="register_users")
@requires_admin
def register_user():
    data = request.json

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    with SessionLocal() as session:
        # check if email exist
        existing = session.query(Employee).filter_by(email=data["email"]).first()
        if existing:
            return jsonify({"error": "User with this email already exists"}), 409

        user = Employee(
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            is_admin=data.get("is_admin", False)
        )

        session.add(user)
        session.commit()

        return jsonify({
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin
        }), 201

@auth_bp.post("/logout", endpoint="logout")
@requires_auth
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200