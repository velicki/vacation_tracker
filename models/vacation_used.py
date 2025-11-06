from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from datetime import datetime


class VacationUsed(Base):
    __tablename__ = "vacation_used"

    id = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_used = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee = relationship("Employee", back_populates="vacation_used")

    def __repr__(self):
        return f"<VacationUsed {self.employee_id} {self.days_used} days>"
