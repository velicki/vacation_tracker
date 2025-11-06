from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from models.base import Base
from werkzeug.security import generate_password_hash, check_password_hash


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)

    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    vacation_totals = relationship("VacationTotal", back_populates="employee", cascade="all, delete")
    vacation_used = relationship("VacationUsed", back_populates="employee", cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Employee {self.username}>"
