from flask import Blueprint, jsonify
from utils.auth import requires_auth

employee_bp = Blueprint("employee_bp", __name__)

@employee_bp.route("/")
@requires_auth()  # any user
def employee_index(user):
    return jsonify({"message": f"Hello {user.username}"})
