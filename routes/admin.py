from flask import Blueprint, jsonify
from utils.auth import requires_auth
from decorators.auth import requires_admin


admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/")
@requires_auth()
@requires_admin  # only admin
def admin_index(user):
    return jsonify({"message": f"Hello Admin {user.username}"})
