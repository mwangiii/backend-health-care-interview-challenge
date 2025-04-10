# -*- coding: utf-8 -*-
import re
from flask import request
from flask_restx import Namespace, Resource
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, api
from app.auth.utils import generate_jwt_token
from utils.error_list import add_error_to_list
from utils.mail import send_email


class UserRegister(Resource):
    def __init__(self, model, role):
        self.model = model
        self.role = role

    def post(self):
        """Register a new user (generic for patient and doctor)"""
        data = request.json
        errors_list = []

        required_fields = ["firstname", "lastname", "email", "phone", "password"]
        if self.role == "doctor":
            required_fields.append("specialization")
        else:
            required_fields.append("date_of_birth")

        for field in required_fields:
            if not data.get(field):
                add_error_to_list(errors_list, field, f"{field.replace('_', ' ').capitalize()} is required")

        if self.model.query.filter_by(email=data.get("email")).first():
            add_error_to_list(errors_list, "email", "Email already in use")

        if self.model.query.filter_by(phone=data.get("phone")).first():
            add_error_to_list(errors_list, "phone", "Phone number already in use")

        if data.get("phone") and not re.match(r"^(\+2547\d{8}|07\d{8})$", data["phone"]):
            add_error_to_list(errors_list, "phone", "Phone number is invalid")

        if data.get("email") and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data["email"]):
            add_error_to_list(errors_list, "email", "Email is invalid")

        if errors_list:
            return {"status": "Bad Request", "message": "Registration unsuccessful", "errors": errors_list}, 400

        hashed_password = generate_password_hash(data.get("password"))

        user_data = {
            "firstname": data.get("firstname"),
            "lastname": data.get("lastname"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "password": hashed_password
        }

        if self.role == "doctor":
            user_data["specialization"] = data.get("specialization")
        else:
            user_data["date_of_birth"] = data.get("date_of_birth")

        new_user = self.model(**user_data)

        try:
            db.session.add(new_user)
            db.session.commit()
            db.session.refresh(new_user)

            response_data = {
                "Id": str(new_user.doctor_id) if self.role == "doctor" else str(new_user.patient_id),
                "employ_id": str(new_user.employee_id) if self.role == "doctor" else None,
                "firstName": new_user.firstname,
                "lastName": new_user.lastname,
                "email": new_user.email,
                "phone": new_user.phone,
            }

            if self.role == "doctor":
                response_data["specialization"] = new_user.specialization
            else:
                response_data["dateOfBirth"] = new_user.date_of_birth.strftime('%Y-%m-%d')

            return {
                "status": "Success",
                "message": "Registration successful",
                "data": {self.role: response_data}
            }, 201

        except Exception as e:
            db.session.rollback()
            return {
                "status": "Internal Server Error",
                "message": "Registration unsuccessful",
                "errors": str(e),
            }, 500


class UserLogin(Resource):
    def __init__(self, model, role):
        self.model = model
        self.role = role

    def post(self):
        """Authenticate a user (generic for patient and doctor)"""
        data = request.json

        required_fields = ['email', 'password']
        if self.role == "doctor":
            required_fields.append('employee_id')

        for field in required_fields:
            if field not in data:
                return {"message": f"{field} is required"}, 400

        email = data['email']
        password = data['password']
        employee_id = data.get('employee_id')

        user = self.model.query.filter_by(email=email).first()

        if not user:
            return {"message": f"{self.role.capitalize()} not found"}, 404

        if self.role == "doctor" and user.employee_id != employee_id:
            return {"message": "Invalid employee ID"}, 400

        if not check_password_hash(user.password, password):
            return {"message": "Invalid password"}, 400

        try:
            if self.role == "doctor":
                jwt_token = generate_jwt_token(user.doctor_id, role=self.role)
            else:
                jwt_token = generate_jwt_token(user.patient_id, role=self.role)

            if not jwt_token:
                return {
                    "status": "Internal Server Error",
                    "message": "Login unsuccessful",
                    "errors": "JWT generation failed"
                }, 500
        except Exception as e:
            return {
                "status": "Internal Server Error",
                "message": "Login unsuccessful",
                "errors": str(e)
            }, 500

        response_data = {
            "accessToken": jwt_token,
            self.role: {
                f"{self.role}Id": str(user.doctor_id if self.role == "doctor" else user.patient_id),
                "firstName": user.firstname,
                "lastName": user.lastname,
                "email": user.email,
                "phone": user.phone
            }
        }

        return {
            "status": "success",
            "message": "Login successful",
            "data": response_data
        }, 200
