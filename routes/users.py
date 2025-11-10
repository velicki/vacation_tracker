from flask import Blueprint, jsonify, request
from utils.auth import requires_auth, requires_admin
from db import SessionLocal
from models.employee import Employee
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, get_jwt
from werkzeug.security import generate_password_hash

users_bp = Blueprint("users", __name__)

@users_bp.get("/", endpoint="list_all_users")
@requires_admin
def list_users():
    session = SessionLocal()
    users = session.query(Employee).all()
    return jsonify([{"id": u.id, "email": u.email, "is_admin": u.is_admin} for u in users])

@users_bp.get("/me", endpoint="my_profile")
@requires_auth
def get_my_profile():
    verify_jwt_in_request()
    user_identity = get_jwt_identity()

    session = SessionLocal()
    user = session.query(Employee).filter_by(id=user_identity).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin
    }), 200


@users_bp.get("/<int:user_id>", endpoint="get_user_by_id")
@requires_admin
def get_user(user_id):

    session = SessionLocal()
    user = session.query(Employee).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin
    }), 200

@users_bp.put("/<int:user_id>", endpoint="update_user")
@requires_auth
def update_user(user_id):
    data = request.get_json()
    session = SessionLocal()

    # Logedin user
    current_user = get_jwt()
    current_user_id = get_jwt_identity()
    is_current_admin = current_user.get("is_admin")

    # target user for update
    user = session.query(Employee).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    is_admin = bool(data.get("is_admin"))
    # Admin can update all
    if is_current_admin:
        # Admin can't remove admin status to himself
        if user_id == int(current_user_id) and is_admin is False:
            return jsonify({"error": "Cannot remove your own admin status"}), 403
        # if admin send new password
        if "password" in data:
            user.password_hash = generate_password_hash(data["password"])
        # if admin change is_admin status
        if "is_admin" in data:
            user.is_admin = data["is_admin"]
    else:
        # Regular user can only change password
        if user_id != int(current_user_id):
            return jsonify({"error": "Cannot change other user's data"}), 403
        if "password" in data:
            user.password_hash = generate_password_hash(data["password"])
        # Check, employee can't change is_admin
        if "is_admin" in data:
            return jsonify({"error": "Cannot change admin status"}), 403

    session.commit()

    return jsonify({
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin
    })

@users_bp.delete("/<int:user_id>", endpoint="delete_user")
@requires_admin
def delete_user(user_id):
    session = SessionLocal()

    # Logedin user
    current_user_id = int(get_jwt_identity())

    # Get target user to delete
    user = session.query(Employee).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user_id == current_user_id:
        return jsonify({"error": "Cannot delete yourself"}), 403

    # Delete user
    session.delete(user)
    session.commit()

    return jsonify({"message": f"User {user.email} deleted successfully"}), 200