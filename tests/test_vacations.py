import io
import csv
import json
import pytest
from datetime import date
from models.vacation_total import VacationTotal
from models.vacation_used import VacationUsed


def test_create_vacation_total_json_success(test_client, create_test_user, make_token, admin_user):
    user = create_test_user(email="john@example.com")
    token = make_token(user_id=admin_user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "year": 2025,
        "total_days": 25
    }

    response = test_client.post("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["employee_id"] == user.id
    assert data["year"] == 2025
    assert data["total_days"] == 25

def test_create_vacation_total_json_missing_fields(test_client, make_token, admin_user):
    token = make_token(user_id=admin_user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"user_id": 1}  # missing year and total_days
    response = test_client.post("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_create_vacation_total_json_duplicate(test_client, create_test_user, make_token, admin_user):
    user = create_test_user(email="jane@example.com")
    token = make_token(user_id=admin_user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    # Create first time
    payload = {"user_id": user.id, "year": 2025, "total_days": 20}
    test_client.post("/vacations/totals", json=payload, headers=headers)

    # Attempt duplicate
    response = test_client.post("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 409
    data = response.get_json()
    assert "error" in data

# ----------------------------
# CSV mode tests
# ----------------------------

def test_create_vacation_total_csv_success(test_client, create_test_user, admin_user, make_token):
    user1 = create_test_user(email="a@example.com")
    user2 = create_test_user(email="b@example.com")
    token = make_token(user_id=admin_user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(["Year", "2025"])  # first row: year
    writer.writerow(["Employee", "Total vacation days"])  # headers
    writer.writerow([user1.email, 10])
    writer.writerow([user2.email, 15])
    csv_data.seek(0)

    response = test_client.post(
        "/vacations/totals",
        data={"file": (io.BytesIO(csv_data.read().encode("utf-8")), "vacations.csv")},
        headers=headers
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["created"] == 2
    assert data["skipped_not_found"] == []
    assert data["skipped_existing"] == []

def test_create_vacation_total_csv_some_missing(test_client, create_test_user, make_token, admin_user):
    user1 = create_test_user(email="c@example.com")
    token = make_token(user_id=admin_user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(["Year", "2025"])
    writer.writerow(["Employee", "Total vacation days"])
    writer.writerow([user1.email, 12])
    writer.writerow(["missing@example.com", 20])
    csv_data.seek(0)

    response = test_client.post(
        "/vacations/totals",
        data={"file": (io.BytesIO(csv_data.read().encode("utf-8")), "vacations.csv")},
        headers=headers
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["created"] == 1
    assert "missing@example.com" in data["skipped_not_found"]


# -------------------------


def test_update_vacation_total_success(test_client, create_test_user, make_token, db_session):
    # Kreiramo korisnika i VacationTotal
    user = create_test_user(email="update@test.com")
    vt = VacationTotal(employee_id=user.id, year=2025, total_days=20, total_days_left=20)

    db_session.add(vt)
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "year": 2025,
        "added_days": 5
    }

    response = test_client.patch("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_days"] == 25
    assert data["total_days_left"] == 25
    assert data["employee_id"] == user.id
    assert data["year"] == 2025

def test_update_vacation_total_missing_fields(test_client, create_test_user, make_token):
    user = create_test_user(email="missing@test.com")
    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"user_id": user.id}  # nedostaju year i added_days
    response = test_client.patch("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_update_vacation_total_not_found(test_client, create_test_user, make_token):
    user = create_test_user(email="nofound@test.com")
    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"user_id": user.id, "year": 2025, "added_days": 5}  # VacationTotal ne postoji
    response = test_client.patch("/vacations/totals", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


# -------------------------


def test_add_vacation_used_success(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="used@test.com")
    # Kreiramo VacationTotal
    vt = VacationTotal(employee_id=user.id, year=2025, total_days=20, total_days_left=20)

    db_session.add(vt)
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "start_date": "2025-07-01",
        "end_date": "2025-07-05"
    }

    response = test_client.post("/vacations/vacation-used", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["days_used"] == 4
    assert data["days_left_now"] == 16

def test_add_vacation_used_not_enough_days(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="notenough@test.com")
    vt = VacationTotal(employee_id=user.id, year=2025, total_days=3, total_days_left=3)

    db_session.add(vt)
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "start_date": "2025-07-01",
        "end_date": "2025-07-05"
    }

    response = test_client.post("/vacations/vacation-used", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert "Not enough vacation days" in data["error"]

def test_add_vacation_used_overlap(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="overlap@test.com")
    vt = VacationTotal(employee_id=user.id, year=2025, total_days=20, total_days_left=20)
    
    db_session.add(vt)
    db_session.commit()

    # Postojeći odmor
    vu = VacationUsed(employee_id=user.id, start_date=date(2025, 7, 1), end_date=date(2025, 7, 5), days_used=5)
    db_session.add(vu)
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "start_date": "2025-07-03",
        "end_date": "2025-07-06"
    }

    response = test_client.post("/vacations/vacation-used", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert "overlaps" in data["error"]

def test_add_vacation_used_no_vacation_total(test_client, create_test_user, make_token):
    user = create_test_user(email="novt@test.com")

    token = make_token(user.id, is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "user_id": user.id,
        "start_date": "2025-07-01",
        "end_date": "2025-07-05"
    }

    response = test_client.post("/vacations/vacation-used", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert "No vacation total" in data["error"]


# -------------------------


def test_get_vacation_overview_success(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="overview@test.com")
    # Dodajemo VacationTotal zapise
    vt1 = VacationTotal(employee_id=user.id, year=2025, total_days=20, total_days_left=15)
    vt2 = VacationTotal(employee_id=user.id, year=2026, total_days=25, total_days_left=25)
    db_session.add_all([vt1, vt2])
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}", headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 2
    assert data[0]["year"] == 2025
    assert data[0]["total_days"] == 20
    assert data[0]["used_days"] == 5  # 20 - 15
    assert data[0]["days_left"] == 15

def test_get_vacation_overview_access_denied(test_client, create_test_user, make_token):
    user = create_test_user(email="overview2@test.com")
    other_user = create_test_user(email="other@test.com")
    token = make_token(other_user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}", headers=headers)
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Access denied"


# -------------------------


def test_get_vacation_year_success(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="year@test.com")
    vt = VacationTotal(employee_id=user.id, year=2025, total_days=20, total_days_left=15)
    vu1 = VacationUsed(employee_id=user.id, start_date=date(2025, 1, 10), end_date=date(2025, 1, 12), days_used=3)
    vu2 = VacationUsed(employee_id=user.id, start_date=date(2025, 2, 5), end_date=date(2025, 2, 6), days_used=2)
    db_session.add_all([vt, vu1, vu2])
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/2025", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["year"] == 2025
    assert data["total_days"] == 20
    assert data["used_days"] == 5
    assert data["days_left"] == 15
    assert len(data["vacations"]) == 2
    assert data["vacations"][0]["days_used"] == 3
    assert data["vacations"][1]["days_used"] == 2

def test_get_vacation_year_no_data(test_client, create_test_user, make_token):
    user = create_test_user(email="nodata@test.com")
    token = make_token(user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/2025", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["year"] == 2025
    assert data["message"] == "No data"

def test_get_vacation_year_access_denied(test_client, create_test_user, make_token):
    user = create_test_user(email="year2@test.com")
    other_user = create_test_user(email="other2@test.com")
    token = make_token(other_user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/2025", headers=headers)
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"] == "Access denied"


# -------------------------


def test_get_used_in_period_success(test_client, create_test_user, make_token, db_session):
    user = create_test_user(email="used@test.com")
    
    vac1 = VacationUsed(employee_id=user.id, start_date=date(2025, 1, 10), end_date=date(2025, 1, 12), days_used=3)
    vac2 = VacationUsed(employee_id=user.id, start_date=date(2025, 1, 15), end_date=date(2025, 1, 16), days_used=2)
    
    db_session.add_all([vac1, vac2])
    db_session.commit()
    db_session.close()

    token = make_token(user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/used?from=2025-01-09&to=2025-01-20", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["user_id"] == user.id
    assert data["days_used"] == 3

def test_get_used_in_period_invalid_date(test_client, create_test_user, make_token):
    user = create_test_user(email="used2@test.com")
    token = make_token(user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/used?from=invalid&to=2025-01-20", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid date format. Use YYYY-MM-DD"

def test_get_used_in_period_access_denied(test_client, create_test_user, make_token):
    user = create_test_user(email="used3@test.com")
    other_user = create_test_user(email="other3@test.com")
    token = make_token(other_user.id, is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get(f"/vacations/{user.id}/used?from=2025-01-01&to=2025-01-31", headers=headers)
    assert response.status_code == 403
    assert response.get_json()["error"] == "Access denied"