import csv
from io import TextIOWrapper
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt
from werkzeug.security import check_password_hash, generate_password_hash

from db import SessionLocal
from models.employee import Employee
from utils.token_blacklist import blacklist
from datetime import timedelta
import re


# Check is email
def is_valid_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


# Initialize first Admin User if db is empty
def initialize_admin():
    session = SessionLocal()

    # Check if any user already exists
    existing_user = session.query(Employee).first()
    if existing_user:
        return jsonify({"error": "Setup already completed. Admin exists."}), 403

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    admin = Employee(
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=True
    )

    session.add(admin)
    session.commit()

    return jsonify({"message": "Initial admin created successfully"}), 201

# Login
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    with SessionLocal() as session:
        user = session.query(Employee).filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(
        identity=str(user.id),
        additional_claims={"is_admin": user.is_admin},
        expires_delta=timedelta(hours=1)
    )
        return jsonify({"access_token": token}), 200

# Add new users
def register_user():
    # Check is there is a file
    file = request.files.get("file")

    # CSV UPLOAD MODE
    if file:
        # Check file in text mode
        wrapped_file = TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(wrapped_file)

        created_count = 0
        skipped_duplicates = 0

        with SessionLocal() as session:
            for row in reader:
                email = row.get("Employee Email")
                password = row.get("Employee Password")
                is_admin_raw = row.get("is_admin", "false").strip().lower()

                # Convert in boolean
                is_admin = is_admin_raw in ["true", "1", "yes"]

                if not email or not password:
                    # Skip, not valid
                    continue

                if not is_valid_email(str(email)):
                    # Skip, not valid
                    continue

                existing = session.query(Employee).filter_by(email=email).first()
                if existing:
                    skipped_duplicates += 1
                    continue

                user = Employee(
                    email=email,
                    password_hash=generate_password_hash(password),
                    is_admin=is_admin
                )

                session.add(user)
                created_count += 1

            session.commit()

        return jsonify({
            "message": "Bulk import completed",
            "created": created_count,
            "duplicates_skipped": skipped_duplicates
        }), 201

    # SINGLE USER JSON MODE

    data = request.json

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    if not is_valid_email(str(data.get("email"))):
        return jsonify({"error": "Invalid email format"}), 400
    
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

# Logout
def logout():
    jti = get_jwt()["jti"]
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200