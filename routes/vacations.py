from flask import Blueprint
from utils.auth import requires_admin, requires_auth
from services import vacations_service


vacations_bp = Blueprint("vacations", __name__)


# Enter total days of vacation for given year
@vacations_bp.post("/totals")
@requires_admin
def create_vacation_total():
    return vacations_service.create_vacation_total()


# Add/update more vacation days for given year
@vacations_bp.patch("/totals")
@requires_admin
def update_vacation_total():
    return vacations_service.update_vacation_total()

  
# Add vacation
@vacations_bp.post("/vacation-used")
@requires_admin
def add_vacation_used():
    return vacations_service.add_vacation_used()


# View vacation total, used, and left days per year
@vacations_bp.get("/<int:user_id>")
@requires_auth
def get_vacation_overview(user_id):
    return vacations_service.get_vacation_overview(user_id)


# List vacation info for given year
@vacations_bp.get("/<int:user_id>/<int:year>")
@requires_auth
def get_vacation_year(user_id, year):
    return vacations_service.get_vacation_year(user_id, year)


# Search used vacation days from-to specific date
# /vacations/<user_id>/used?from=YYYY-MM-DD&to=YYYY-MM-DD
@vacations_bp.get("/<int:user_id>/used")
@requires_auth
def get_used_in_period(user_id):
    return vacations_service.get_used_in_period(user_id)