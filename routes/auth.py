from flask import Blueprint
from flask_jwt_extended import jwt_required
from utils.auth import requires_admin, requires_auth
from services import auth_service 

auth_bp = Blueprint("auth", __name__)


# Initialize first Admin User if db is empty
@auth_bp.post("/initialize")
def initialize_admin():
    return auth_service .initialize_admin()
    

# Login
@auth_bp.post("/login", endpoint="login")
def login():
    return auth_service.login()


# Add new users
@auth_bp.post("/register", endpoint="register_users")
@requires_admin
def register_user():
    return auth_service.register_user()
    
# Logout
@auth_bp.post("/logout", endpoint="logout")
@requires_auth
@jwt_required()
def logout():
    return auth_service.logout()
    