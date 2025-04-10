from flask_restx import fields
from app import api
from marshmallow import Schema, fields as ma_fields, ValidationError, validates
from datetime import datetime

# RESTX API Models for Swagger documentation
doctor_register_model = api.model('DoctorRegister', {
    'firstname': fields.String(required=True, description='First name of the doctor'),
    'lastname': fields.String(required=True, description='Last name of the doctor'),
    'email': fields.String(required=True, description='Doctor email address'),
    'phone': fields.String(required=True, description='Doctor phone number'),
    'password': fields.String(required=True, description='Password for the doctor'),
    'specialization': fields.String(required=True, description='Doctor specialization'),
})

doctor_availability_model = api.model('DoctorAvailability', {
    'availability_start': fields.String(required=True, description='Start time (HH:MM)'),
    'availability_end': fields.String(required=True, description='End time (HH:MM)'),
    'days_available': fields.List(fields.String, required=True, description='Days available'),
})

doctor_details_response = api.model('DoctorDetailsResponse', {
    'doctor_id': fields.String(description='Unique identifier'),
    'firstname': fields.String(description='First name'),
    'lastname': fields.String(description='Last name'),
    'specialization': fields.String(description='Specialization'),
    'availability_start': fields.String(description='Start time (HH:MM)'),
    'availability_end': fields.String(description='End time (HH:MM)'),
    'days_available': fields.List(fields.String, description='Days available'),
})

doctor_availability_response = api.model('DoctorAvailabilityResponse', {
    'doctor_id': fields.String(description='Unique identifier'),
    'availability_start': fields.String(description='Start time'),
    'availability_end': fields.String(description='End time'),
    'days_available': fields.List(fields.String, description='Days available'),
})


# Marshmallow Schema for validation logic
class DoctorAvailabilitySchema(Schema):
    availability_start = ma_fields.String(required=True)
    availability_end = ma_fields.String(required=True)
    days_available = ma_fields.List(ma_fields.String(), required=True)

    @validates("availability_start")
    def validate_start_time(self, value):
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise ValidationError("availability_start must be in HH:MM format")

    @validates("availability_end")
    def validate_end_time(self, value):
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise ValidationError("availability_end must be in HH:MM format")

    @validates("days_available")
    def validate_days(self, value):
        if not value or not isinstance(value, list):
            raise ValidationError("days_available must be a non-empty list of strings")
