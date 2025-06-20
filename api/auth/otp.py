import os
import smtplib

import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pyotp import TOTP
# from api.auth.email_config import SMTP_EMAIL,SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
# from email.message import EmailMessage
from api.auth import authutils, model
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv


# EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")


load_dotenv()



class EmailError(Exception):
    pass


OTP_SECRET_KEY = os.getenv("OTP_SECRET_KEY", "")
totp = TOTP(OTP_SECRET_KEY, interval=1800)


def generate_and_store_otp(user: model.DBUser, db: Session) -> str:
    code = totp.now()
    hashed_code = authutils.pwd_context.hash(code)
    user.hashed_otp = hashed_code
    db.commit()
    db.refresh(user)
    return code


def verify_otp(entered_otp: str, user: model.DBUser, db: Session):
    stored_otp = user.hashed_otp

    if stored_otp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no otp entered"
        )

    if authutils.verify_password(entered_otp, stored_otp) is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="wrong otp pls try again"
        )

    return totp.verify(entered_otp)


async def send_otp_to_user(subject: str, body: str, recipient_email: str):
    try:
        # Create message using MIMEMultipart for better compatibility
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = SMTP_EMAIL
        message["To"] = recipient_email
        
        # Add body to email
        message.attach(MIMEText(body, "plain"))
        
        print(f"SMTP Config - Server: {SMTP_SERVER}, Port: {SMTP_PORT}")
        print(f"From: {SMTP_EMAIL}, To: {recipient_email}")
        
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Use SMTP_SSL for port 465 or SMTP with starttls for port 587
        if int(SMTP_PORT) == 465:
            # Gmail SMTP SSL
            with smtplib.SMTP_SSL(SMTP_SERVER, int(SMTP_PORT), context=context) as server:
                print("SSL connection established")
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                print("Authentication successful")
                server.sendmail(SMTP_EMAIL, recipient_email, message.as_string())
                print("Authentication successful")
        else:
            # Gmail SMTP with STARTTLS (port 587)
            with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
                server.starttls(context=context)
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, recipient_email, message.as_string())
        
        return "Message delivered successfully"
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication failed: {e}")
        print("Please check your email and app password")
        raise EmailError("Authentication failed - check email credentials")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Recipients refused: {e}")
        raise EmailError("Invalid recipient email address")
    except smtplib.SMTPServerDisconnected as e:
        print(f"SMTP server disconnected: {e}")
        raise EmailError("Email server connection lost")
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        raise EmailError(f"Email sending failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise EmailError(f"Failed to send email: {str(e)}")
