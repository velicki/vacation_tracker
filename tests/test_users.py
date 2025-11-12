import pytest
from flask_jwt_extended import create_access_token
from datetime import timedelta

def test_list_users_success(test_client, admin_user, test_app):
    with test_app.app_context():
        token = create_access_token(
            identity=str(admin_user.id),
            additional_claims={"is_admin": True},
            expires_delta=timedelta(hours=1)
        )

        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/users/", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert any(u["email"] == admin_user.email for u in data)


def test_list_users_requires_admin(test_client, create_test_user, test_app):
    user = create_test_user(email="ordinary@test.com", is_admin=False)

    with test_app.app_context():
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"is_admin": False},
            expires_delta=timedelta(hours=1)
        )

        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/users/", headers=headers)

        assert response.status_code == 403


# ------------------------------


def test_get_my_profile_success(test_client, create_test_user, test_app):
    user = create_test_user(email="me@test.com", is_admin=False)

    with test_app.app_context():
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"is_admin": user.is_admin},
            expires_delta=timedelta(hours=1)
        )

        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/users/me", headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "me@test.com"
        assert data["id"] == user.id
        assert data["is_admin"] is False


def test_get_my_profile_user_not_found(test_client, test_app):
    with test_app.app_context():
        token = create_access_token(
            identity="99999",
            additional_claims={"is_admin": False},
            expires_delta=timedelta(hours=1)
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/users/me", headers=headers)

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "User not found"


def test_get_my_profile_unauthorized(test_client):
    response = test_client.get("/users/me")
    assert response.status_code == 401


# ------------------------------


def test_get_user_by_id_success(test_client, create_test_user, admin_token):
    user = create_test_user(email="user1@test.com", is_admin=False)

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = test_client.get(f"/users/{user.id}", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user.id
    assert data["email"] == "user1@test.com"
    assert data["is_admin"] is False


def test_get_user_by_id_not_found(test_client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = test_client.get("/users/99999", headers=headers)  # nepostojeći ID

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "User not found"


def test_get_user_by_id_unauthorized(test_client, create_test_user, make_token):
    user = create_test_user(email="user2@test.com", is_admin=False)

    token = make_token(user.id, is_admin=False)

    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"/users/{user.id}", headers=headers)

    assert response.status_code == 403


# ------------------------------


def test_admin_update_other_user(test_client, create_test_user, admin_token):
    user = create_test_user(email="user1@test.com", is_admin=False)

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"password": "newpass", "is_admin": True}
    response = test_client.put(f"/users/{user.id}", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user.id
    assert data["is_admin"] is True


def test_admin_cannot_remove_own_admin(test_client, admin_token, admin_user):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"is_admin": False}

    response = test_client.put(f"/users/{admin_user.id}", json=payload, headers=headers)

    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Cannot remove your own admin status"


def test_nonadmin_update_own_password(test_client, create_test_user, make_token):
    user = create_test_user(email="user2@test.com", is_admin=False)

    token = make_token(user.id, is_admin=False)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"password": "mypassword"}
    response = test_client.put(f"/users/{user.id}", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user.id


def test_nonadmin_cannot_change_is_admin_or_other_user(test_client, create_test_user, make_token):
    user = create_test_user(email="user3@test.com", is_admin=False)
    other_user = create_test_user(email="user4@test.com", is_admin=False)

    token = make_token(user.id, is_admin=False)

    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"is_admin": True}
    resp = test_client.put(f"/users/{user.id}", json=payload, headers=headers)
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "Cannot change admin status"

    payload = {"password": "hack"}
    resp2 = test_client.put(f"/users/{other_user.id}", json=payload, headers=headers)
    assert resp2.status_code == 403
    assert resp2.get_json()["error"] == "Cannot change other user's data"


def test_update_user_not_found(test_client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"password": "newpass"}
    response = test_client.put("/users/99999", json=payload, headers=headers)

    assert response.status_code == 404
    assert response.get_json()["error"] == "User not found"


# ------------------------------


def test_admin_delete_other_user(test_client, create_test_user, admin_user, make_token):
    user = create_test_user(email="tobedeleted@test.com", is_admin=False)

    token = make_token(user_id=admin_user.id, is_admin=True)

    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"/users/{user.id}", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == f"User {user.email} deleted successfully"


def test_admin_cannot_delete_self(test_client, admin_user, make_token):
    token = make_token(user_id=admin_user.id, is_admin=True)

    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"/users/{admin_user.id}", headers=headers)

    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Cannot delete yourself"


def test_delete_user_not_found(test_client,admin_user, make_token):
    token = make_token(user_id=admin_user.id, is_admin=True)

    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete("/users/99999", headers=headers)

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "User not found"
