# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app import db


class Appointment(db.Model):
    """
    Represents an appointment in the healthcare system.
    """
    appointment_id = Column(UUID, primary_key=True, default=uuid.uuid4, unique=True)
    patient_id = Column(UUID, ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = Column(UUID, ForeignKey('doctors.doctor_id'), nullable=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(String(50), default='booked')
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment {self.appointment_id}>"
