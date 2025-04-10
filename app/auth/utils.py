from datetime import datetime, timedelta
import jwt
from flask import current_app
from config import Config

def generate_jwt_token(user_id, role):
    """
    Generate a JWT token for a user.

    Args:
        user_id (int): The ID of the user (patient, doctor, or admin).
        role (str): The role of the user ("patient", "doctor", or "admin").

    Returns:
        str: The generated JWT token.
    """
    try:
        jwt_secret_key = Config.JWT_SECRET_KEY
        if not jwt_secret_key:
            raise Exception("JWT_SECRET_KEY is not set in the environment variables.")
        
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "sub": str(user_id),
            "role": role
        }

        jwt_token = jwt.encode(payload, jwt_secret_key, algorithm="HS256")
        return jwt_token
    except Exception as e:
        print(f"JWT Generation Error: {e}")
        return None
