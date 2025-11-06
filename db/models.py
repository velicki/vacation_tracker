# from db import db

# class Employee(db.Model):
#     __tablename__ = "employees"

#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True, nullable=False)
#     password_hash = db.Column(db.String(255), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)

#     # relationships
#     vacation_totals = db.relationship("VacationTotal", back_populates="employee", cascade="all, delete-orphan")
#     vacation_used = db.relationship("VacationUsed", back_populates="employee", cascade="all, delete-orphan")

# class VacationTotal(db.Model):
#     __tablename__ = "vacation_totals"

#     id = db.Column(db.Integer, primary_key=True)
#     employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
#     year = db.Column(db.Integer, nullable=False)
#     total_days = db.Column(db.Integer, nullable=False)

#     employee = db.relationship("Employee", back_populates="vacation_totals")

#     __table_args__ = (
#         db.UniqueConstraint("employee_id", "year", name="unique_employee_year"),  # one entry per year
#     )


# class VacationUsed(db.Model):
#     __tablename__ = "vacation_used"

#     id = db.Column(db.Integer, primary_key=True)
#     employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
#     date_from = db.Column(db.Date, nullable=False)
#     date_to = db.Column(db.Date, nullable=False)
#     used_days = db.Column(db.Integer, nullable=False)  # can automatically calculate 

#     employee = db.relationship("Employee", back_populates="vacation_used")

#     def calculate_used_days(self):
#         """If there is no data for used_days, calculate number of days"""
#         return (self.date_to - self.date_from).days + 1

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         if "used_days" not in kwargs:
#             self.used_days = self.calculate_used_days()