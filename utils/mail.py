
from flask_mail import Message, Mail
from flask import current_app

mail = Mail()

def send_email(subject, recipient, body):
    """Send an email to a user."""
    if not recipient:
        return False 

    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body,
            sender=current_app.config["MAIL_DEFAULT_SENDER"]
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False
