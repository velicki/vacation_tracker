from flask import Blueprint, request, jsonify
from utils.auth import requires_admin, requires_auth
from db import SessionLocal
from models.employee import Employee
from models.vacation_total import VacationTotal
from models.vacation_used import VacationUsed
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta, datetime


def calculate_workdays(start_date, end_date):
    day_count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0-4 mo-fr
            day_count += 1
        current += timedelta(days=1)
    return day_count

def overlap_is_only_weekends(start, end):
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0-4 mo-fr
            return False
        current += timedelta(days=1)
    return True

def can_view(user_id):
    """Returns True if current user is allowed to view given user_id"""
    jwt_data = get_jwt()
    current_user_id = int(get_jwt_identity())
    is_admin = jwt_data.get("is_admin", False)

    return is_admin or (current_user_id == user_id)

vacations_bp = Blueprint("vacations", __name__)

@vacations_bp.post("/totals")
@requires_admin
def create_vacation_total():
    data = request.json
    user_id = data.get("user_id")
    year = data.get("year")
    total_days = data.get("total_days")

    if not user_id or not year or total_days is None:
        return jsonify({"error": "user_id, year and total_days are required"}), 400

    with SessionLocal() as session:
        existing = session.query(VacationTotal).filter_by(employee_id=user_id, year=year).first()
        if existing:
            return jsonify({"error": "Vacation total already set for this user and year"}), 409

        vt = VacationTotal(
            employee_id=user_id,
            year=year,
            total_days=total_days,
            total_days_left=total_days
        )

        session.add(vt)
        session.commit()

        return jsonify({
            "message": "Vacation total created",
            "employee_id": user_id,
            "year": year,
            "total_days": total_days
        }), 201
    
@vacations_bp.patch("/totals")
@requires_admin
def update_vacation_total():
    data = request.json
    user_id = data.get("user_id")
    year = data.get("year")
    added_days = data.get("added_days")

    if not user_id or not year or added_days is None:
        return jsonify({"error": "user_id, year and added_days are required"}), 400

    with SessionLocal() as session:
        vt = session.query(VacationTotal).filter_by(employee_id=user_id, year=year).first()
        if not vt:
            return jsonify({"error": "Vacation total for this user and year not found"}), 404

        vt.total_days += added_days
        vt.total_days_left += added_days

        session.commit()

        return jsonify({
            "message": "Vacation total updated",
            "employee_id": user_id,
            "year": year,
            "total_days": vt.total_days,
            "total_days_left": vt.total_days_left
        }), 200
    

@vacations_bp.post("/<int:user_id>/vacation-used")
@requires_admin
def add_vacation_used(user_id):
    data = request.get_json()

    try:
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if end_date < start_date:
        return jsonify({"error": "end_date cannot be before start_date"}), 400

    year = start_date.year

    with SessionLocal() as session:
        vacation_total = session.query(VacationTotal).filter_by(employee_id=user_id, year=year).first()
        if not vacation_total:
            return jsonify({"error": f"No vacation total defined for year {year}"}), 400
        
        # check for overlap
        existing_vacations = (
            session.query(VacationUsed)
            .filter(
                VacationUsed.employee_id == user_id,
                VacationUsed.end_date >= start_date,
                VacationUsed.start_date <= end_date
            )
            .all()
        )

        for existing in existing_vacations:
            overlap_start = max(existing.start_date, start_date)
            overlap_end = min(existing.end_date, end_date)

            if overlap_start <= overlap_end:
                if not overlap_is_only_weekends(overlap_start, overlap_end):
                    return jsonify({
                        "error": "Vacation period overlaps with an existing vacation in workdays",
                        "overlap_start": str(overlap_start),
                        "overlap_end": str(overlap_end)
                    }), 400

        days_used = calculate_workdays(start_date, end_date)

        if vacation_total.total_days_left < days_used:
            return jsonify({
                "error": "Not enough vacation days left",
                "days_left": vacation_total.total_days_left,
                "days_needed": days_used
            }), 400

        vacation = VacationUsed(
            start_date=start_date,
           	end_date=end_date,
            days_used=days_used,
            employee_id=user_id
        )
        session.add(vacation)

        vacation_total.total_days_left -= days_used

        session.commit()

        return jsonify({
            "message": "Vacation entry added",
            "days_used": days_used,
            "days_left_now": vacation_total.total_days_left
        }), 201
    
@vacations_bp.get("/<int:user_id>")
@requires_auth
def get_vacation_overview(user_id):
    if not can_view(user_id):
        return jsonify({"error": "Access denied"}), 403

    with SessionLocal() as session:
        totals = session.query(VacationTotal).filter_by(employee_id=user_id).all()

        result = []
        for vt in totals:
            used_days = vt.total_days - vt.total_days_left

            result.append({
                "year": vt.year,
                "total_days": vt.total_days,
                "used_days": used_days,
                "days_left": vt.total_days_left,
            })

        return jsonify(result), 200
    

@vacations_bp.get("/<int:user_id>/<int:year>")
@requires_auth
def get_vacation_year(user_id, year):
    if not can_view(user_id):
        return jsonify({"error": "Access denied"}), 403

    with SessionLocal() as session:
        vt = session.query(VacationTotal).filter_by(employee_id=user_id, year=year).first()
        if not vt:
            return jsonify({"year": year, "message": "No data"}), 200

        used_days = vt.total_days - vt.total_days_left

        vacations = (
            session.query(VacationUsed)
            .filter(
                VacationUsed.employee_id == user_id,
                VacationUsed.start_date >= datetime(year, 1, 1).date(),
                VacationUsed.end_date <= datetime(year, 12, 31).date()
            )
            .order_by(VacationUsed.start_date.asc())
            .all()
        )

        vacation_list = [
            {
                "id": v.id,
                "start_date": v.start_date.isoformat(),
                "end_date": v.end_date.isoformat(),
                "days_used": v.days_used,
            }
            for v in vacations
        ]

        return jsonify({
            "year": year,
            "total_days": vt.total_days,
            "used_days": used_days,
            "days_left": vt.total_days_left,
            "vacations": vacation_list
        }), 200


# /vacations/<user_id>/used?from=YYYY-MM-DD&to=YYYY-MM-DD
@vacations_bp.get("/<int:user_id>/used")
@requires_auth
def get_used_in_period(user_id):
    if not can_view(user_id):
        return jsonify({"error": "Access denied"}), 403

    start = request.args.get("from")
    end = request.args.get("to")

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    with SessionLocal() as session:
        vacations = (
            session.query(VacationUsed)
            .filter(
                VacationUsed.employee_id == user_id,
                VacationUsed.end_date >= start_date,
                VacationUsed.start_date <= end_date
            )
            .all()
        )

        total_used = 0

        for vac in vacations:
            overlap_start = max(vac.start_date, start_date)
            overlap_end = min(vac.end_date, end_date)
            total_used += calculate_workdays(overlap_start, overlap_end)

        return jsonify({
            "user_id": user_id,
            "from": start,
            "to": end,
            "days_used": total_used
        }), 200
