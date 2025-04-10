# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, time
from sqlalchemy import Column, Integer, String, DateTime, Sequence, Time, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app import db

employee_id_seq = Sequence('employee_id_seq')


class Doctor(db.Model):
    """
    Represents a doctor in the healthcare system.
    """
    __tablename__ = 'doctors'

    doctor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    employee_id = Column(Integer, unique=True, nullable=False, server_default=employee_id_seq.next_value())
    image = Column(Text, nullable=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    availability_start = Column(Time, nullable=True)
    availability_end = Column(Time, nullable=True)
    days_available = Column(String(100), nullable=True)

    appointments = relationship("Appointment", back_populates="doctor")

    def __repr__(self):
        return f"<Doctor {self.firstname} {self.lastname}>"
