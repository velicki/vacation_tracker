from flask import Blueprint
from utils.auth import requires_auth, requires_admin
from services import users_service

users_bp = Blueprint("users", __name__)

# List all users
@users_bp.get("/", endpoint="list_all_users")
@requires_admin
def list_users():
    return users_service.list_users()
    
# Show logedin user profile
@users_bp.get("/me", endpoint="my_profile")
@requires_auth
def get_my_profile():
    return users_service.get_my_profile()

# Show one user profile
@users_bp.get("/<int:user_id>", endpoint="get_user_by_id")
@requires_admin
def get_user(user_id):
    return users_service.get_user(user_id)
    
# Update profile
@users_bp.put("/<int:user_id>", endpoint="update_user")
@requires_auth
def update_user(user_id):
    return users_service.update_user(user_id)

# Delete user
@users_bp.delete("/<int:user_id>", endpoint="delete_user")
@requires_admin
def delete_user(user_id):
    return users_service.delete_user(user_id)