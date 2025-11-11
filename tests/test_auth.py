import io
import json
import csv
import pytest
from flask_jwt_extended import create_access_token, get_jti
from utils.token_blacklist import blacklist
from datetime import timedelta
from db import SessionLocal
from models.employee import Employee


def test_initialize_admin_success(test_client):
    payload = {
        "email": "admin@test.com",
        "password": "admin123"
    }

    response = test_client.post(
        "/auth/initialize",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "Initial admin created successfully"

    session = SessionLocal()
    user = session.query(Employee).first()
    session.close()

    assert user is not None
    assert user.email == "admin@test.com"
    assert user.is_admin is True


def test_initialize_admin_missing_fields(test_client):
    payload = {"email": "admin2@test.com"}

    response = test_client.post(
        "/auth/initialize",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email and password required"


def test_initialize_admin_already_exists(test_client):
    # Prvo kreiramo admina ručno
    session = SessionLocal()
    admin = Employee(email="exists@test.com", is_admin=True)
    admin.set_password("pass123")
    session.add(admin)
    session.commit()
    session.close()

    # Pokušavamo ponovnu inicijalizaciju
    payload = {
        "email": "newadmin@test.com",
        "password": "secret"
    }

    response = test_client.post(
        "/auth/initialize",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Setup already completed. Admin exists."


# ------------------------------------


def test_login_success(test_client, create_test_user):
    create_test_user(email="valid@example.com", password="mypassword")

    response = test_client.post(
        "/auth/login",
        json={"email": "valid@example.com", "password": "mypassword"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data


def test_login_invalid_password(test_client, create_test_user):
    create_test_user(email="john@example.com", password="correct-pass")

    response = test_client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "wrong-pass"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials"


def test_login_invalid_email(test_client):
    response = test_client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "whatever"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials"


def test_login_missing_fields(test_client):
    response = test_client.post("/auth/login", json={})
    assert response.status_code == 401  # Flask vraća 400 jer request.json.get ne daje vrednosti


# ------------------------------------


def test_register_single_user_success(test_client, admin_token):
    response = test_client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "123", "is_admin": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == "new@example.com"
    assert data["is_admin"] is True


def test_register_single_user_duplicate(test_client, admin_token, create_test_user):
    create_test_user(email="exists@example.com")

    response = test_client.post(
        "/auth/register",
        json={"email": "exists@example.com", "password": "123"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "User with this email already exists"


def test_register_single_user_missing_fields(test_client, admin_token):
    response = test_client.post(
        "/auth/register",
        json={"email": ""},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Email and password are required"


def test_register_csv_bulk_success(test_client, admin_token):
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(["Employee Email", "Employee Password", "is_admin"])
    writer.writerow(["one@example.com", "1111", "true"])
    writer.writerow(["two@example.com", "2222", "false"])
    csv_data.seek(0)

    response = test_client.post(
        "/auth/register",
        data={"file": (io.BytesIO(csv_data.read().encode("utf-8")), "bulk.csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["created"] == 2
    assert data["duplicates_skipped"] == 0


def test_register_requires_admin(test_client, create_test_user, make_token):
    user = create_test_user(email="notadmin@example.com", is_admin=False)
    token = make_token(user.id, is_admin=False)

    response = test_client.post(
        "/auth/register",
        json={"email": "shouldfail@example.com", "password": "abc"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


# ------------------------------------


def test_logout_success(test_client, admin_user, test_app):
    # Kreiramo token
    with test_app.app_context():
        token = create_access_token(
            identity=str(admin_user.id),
            additional_claims={"is_admin": True},
            expires_delta=timedelta(hours=1)
        )

        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.post("/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["msg"] == "Successfully logged out"

        # Proveravamo da li je JTI dodat u blacklist
        jti = get_jti(token)
        assert jti in blacklist


def test_logout_no_token(test_client):
    # Ako ne pošaljemo token
    response = test_client.post("/auth/logout")
    assert response.status_code == 401  # Unauthorized