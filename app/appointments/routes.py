from flask_restx import Namespace, Resource
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
import jwt
from app.appointments.models import Appointment
from app import db
from datetime import datetime
from utils.mail import send_email
from config import Config
from app.patients.models import Patient
from app.doctors.models import Doctor
from app.appointments.schemas import (
    appointment_model,
    book_appointment_model,
    cancel_appointment_response_model,
    reschedule_appointment_model,
    error_response_model,
    appointments_list_model,
)

appointment_namespace = Namespace("appointments", description="Appointments related operations")

appointment_namespace.add_model("Appointment", appointment_model)
appointment_namespace.add_model("BookAppointment", book_appointment_model)
appointment_namespace.add_model("RescheduleAppointment", reschedule_appointment_model)
appointment_namespace.add_model("CancelAppointmentResponse", cancel_appointment_response_model)
appointment_namespace.add_model("ErrorResponse", error_response_model)
appointment_namespace.add_model("AppointmentsList", appointments_list_model)


@appointment_namespace.route("/")
class AppointmentsResource(Resource):
    @jwt_required()
    @appointment_namespace.response(200, "Success", appointments_list_model)
    def get(self):
        """
        Get all appointments related to the logged-in user.
        """
        current_user_id = get_jwt_identity()
        user = Patient.query.filter_by(patient_id=current_user_id).first() or Doctor.query.filter_by(doctor_id=current_user_id).first()

        if not user:
            return {"status": "error", "message": "User not found"}, 404

        user_role = "patient" if isinstance(user, Patient) else "doctor"
        user_id = user.patient_id if isinstance(user, Patient) else user.doctor_id

        if user_role == "doctor":
            appointments = Appointment.query.filter_by(doctor_id=user_id).all()
        elif user_role == "patient":
            appointments = Appointment.query.filter_by(patient_id=user_id).all()
        else:
            return {"status": "error", "message": "Unauthorized"}, 403

        # If no appointments, return an empty list with a success message
        if not appointments:
            return {
                "status": "success",
                "message": "Here is where we will display the appointments",
                "data": {"appointments": []},
            }, 200

        appointment_list = [
            {
                "appointmentId": str(appointment.appointment_id),
                "patientId": str(appointment.patient_id),
                "doctorId": str(appointment.doctor_id),
                "date": appointment.date.strftime("%Y-%m-%d"),
                "time": appointment.time.strftime("%H:%M"),
                "status": appointment.status,
            }
            for appointment in appointments
        ]

        return {
            "status": "success",
            "message": "Appointments retrieved successfully",
            "data": {"appointments": appointment_list},
        }, 200


@appointment_namespace.route("/book")
class BookAppointmentResource(Resource):
    @jwt_required()
    @appointment_namespace.expect(book_appointment_model)
    @appointment_namespace.response(201, "Appointment booked successfully", appointment_model)
    @appointment_namespace.response(400, "Invalid input", error_response_model)
    @appointment_namespace.response(404, "Patient not found", error_response_model)
    @appointment_namespace.response(409, "Appointment already exists", error_response_model)
    def post(self):
        """
        Book an appointment (Patient only).
        """
        current_user = get_jwt_identity()
        user_role = current_user.get("role")
        user = Patient.query.filter_by(patient_id=current_user.get("id")).first() or Doctor.query.filter_by(doctor_id=current_user.get("id")).first()

        if not user:
            return {"status": "error", "message": "User not found"}, 404

        if user_role != "patient":
            return {"status": "error", "message": "Unauthorized, only patients can book appointments"}, 403

        data = request.get_json()
        date = data.get("date")
        time = data.get("time")
        doctor_id = data.get("doctor_id")

        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time, "%H:%M").time()
        except ValueError as e:
            return {"status": "error", "message": str(e)}, 400

        existing_appointment = Appointment.query.filter_by(
            date=appointment_date, time=appointment_time, doctor_id=doctor_id
        ).first()

        if existing_appointment:
            return {"status": "error", "message": "Appointment already exists"}, 409

        new_appointment = Appointment(
            patient_id=user.patient_id,
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            status="booked",
        )

        db.session.add(new_appointment)
        db.session.commit()

        send_email(
            recipient=user.email,
            subject="Appointment Confirmation",
            body=f"Your appointment is booked for {date} at {time}.",
        )

        return {
            "status": "success",
            "message": "Appointment booked successfully",
            "data": {
                "appointmentId": str(new_appointment.appointment_id),
                "patientId": str(new_appointment.patient_id),
                "doctorId": str(new_appointment.doctor_id),
                "date": new_appointment.date.strftime("%Y-%m-%d"),
                "time": new_appointment.time.strftime("%H:%M"),
                "status": new_appointment.status,
            },
        }, 201


@appointment_namespace.route("/cancel/<uuid:appointment_id>")
class CancelAppointmentResource(Resource):
    @jwt_required()
    @appointment_namespace.response(200, "Appointment cancelled successfully", cancel_appointment_response_model)
    @appointment_namespace.response(404, "Appointment not found", error_response_model)
    @appointment_namespace.response(403, "You are not authorized to cancel this appointment", error_response_model)
    def delete(self, appointment_id):
        """
        Cancel an appointment (Patient only).
        """
        current_user_id = get_jwt_identity()
        user = Patient.query.filter_by(patient_id=current_user_id).first()

        if not user:
            return {"status": "error", "message": "User not found"}, 404

        user_role = "patient" if isinstance(user, Patient) else "doctor"
        if user_role != "patient":
            return {"status": "error", "message": "Unauthorized, only patients can cancel appointments"}, 403

        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"status": "error", "message": f"Appointment with ID {appointment_id} not found"}, 404

        if str(appointment.patient_id) != str(current_user_id):
            return {"status": "error", "message": "You are not authorized to cancel this appointment"}, 403

        patient = Patient.query.filter_by(patient_id=appointment.patient_id).first()
        if not patient:
            return {"status": "error", "message": "Patient not found"}, 404

        db.session.delete(appointment)
        db.session.commit()

        send_email(
            recipient=patient.email,
            subject="Appointment Cancellation",
            body="Your appointment has been cancelled.",
        )

        return {
            "status": "success",
            "message": "Appointment cancelled successfully",
            "data": {"appointmentId": str(appointment_id)},
        }, 200


@appointment_namespace.route("/reschedule/<uuid:appointment_id>")
class RescheduleAppointmentResource(Resource):
    @jwt_required()
    @appointment_namespace.expect(reschedule_appointment_model)
    @appointment_namespace.response(200, "Appointment rescheduled successfully", appointment_model)
    @appointment_namespace.response(404, "Appointment not found", error_response_model)
    @appointment_namespace.response(400, "Invalid input", error_response_model)
    @appointment_namespace.response(403, "You are not authorized to reschedule this appointment", error_response_model)
    def put(self, appointment_id):
        """
        Reschedule an appointment (Patient only).
        """
        current_user_id = get_jwt_identity()
        user = Patient.query.filter_by(patient_id=current_user_id).first()

        if not user:
            return {"status": "error", "message": "User not found"}, 404

        user_role = "patient" if isinstance(user, Patient) else "doctor"
        if user_role != "patient":
            return {"status": "error", "message": "Unauthorized, only patients can reschedule appointments"}, 403

        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"status": "error", "message": f"Appointment with ID {appointment_id} not found"}, 404

        if str(appointment.patient_id) != str(current_user_id):
            return {"status": "error", "message": "You are not authorized to reschedule this appointment"}, 403

        data = request.get_json()
        date = data.get("date")
        time = data.get("time")

        try:
            new_date = datetime.strptime(date, "%Y-%m-%d").date()
            new_time = datetime.strptime(time, "%H:%M").time()
        except ValueError as e:
            return {"status": "error", "message": str(e)}, 400

        existing_appointment = Appointment.query.filter_by(
            date=new_date, time=new_time, doctor_id=appointment.doctor_id
        ).first()

        if existing_appointment:
            return {"status": "error", "message": "Appointment already exists at this time"}, 409

        appointment.date = new_date
        appointment.time = new_time
        db.session.commit()

        patient = Patient.query.filter_by(patient_id=appointment.patient_id).first()
        if not patient:
            return {"status": "error", "message": "Patient not found"}, 404

        send_email(
            recipient=patient.email,
            subject="Appointment Rescheduled",
            body=f"Your appointment has been rescheduled to {new_date} at {new_time}.",
        )

        return {
            "status": "success",
            "message": "Appointment rescheduled successfully",
            "data": {
                "appointmentId": str(appointment.appointment_id),
                "patientId": str(appointment.patient_id),
                "doctorId": str(appointment.doctor_id),
                "date": appointment.date.strftime("%Y-%m-%d"),
                "time": appointment.time.strftime("%H:%M"),
                "status": appointment.status,
            },
        }, 200


@appointment_namespace.route("/<uuid:appointment_id>")
class ViewAppointmentResource(Resource):
    @appointment_namespace.response(200, "Appointment details retrieved successfully", appointment_model)
    @appointment_namespace.response(404, "Appointment not found", error_response_model)
    @appointment_namespace.response(403, "You are not authorized to view this appointment", error_response_model)
    def get(self, appointment_id):
        """
        Get appointment details (Patient only).
        """
        current_user = get_jwt_identity()
        user_role = current_user.get("role")
        user = Patient.query.filter_by(patient_id=current_user.get("id")).first() or Doctor.query.filter_by(doctor_id=current_user.get("id")).first()

        if not user:
            return {"status": "error", "message": "User not found"}, 404

        if user_role != "patient":
            return {"status": "error", "message": "Unauthorized, only patients can view appointment details"}, 403

        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"status": "error", "message": f"Appointment with ID {appointment_id} not found"}, 404

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return {"status": "error", "message": "Authorization header missing"}, 400

        try:
            token = auth_header.split(" ")[1]
            decoded_token = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            patient_id_from_token = decoded_token.get("sub")
        except (IndexError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return {"status": "error", "message": "Invalid or expired token"}, 401

        if str(appointment.patient_id) != str(patient_id_from_token):
            return {"status": "error", "message": "You are not authorized to view this appointment"}, 403

        return {
            "status": "success",
            "message": "Appointment details retrieved successfully",
            "data": {
                "appointmentId": str(appointment.appointment_id),
                "patientId": str(appointment.patient_id),
                "doctorId": str(appointment.doctor_id),
                "date": appointment.date.strftime("%Y-%m-%d"),
                "time": appointment.time.strftime("%H:%M"),
                "status": appointment.status,
            },
        }, 200
