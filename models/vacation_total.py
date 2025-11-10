from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class VacationTotal(Base):
    __tablename__ = "vacation_totals"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)
    total_days_left = Column(Integer, nullable=False)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee = relationship("Employee", back_populates="vacation_totals")

    def __repr__(self):
        return f"<VacationTotal {self.employee_id} {self.year}: {self.total_days}>"
