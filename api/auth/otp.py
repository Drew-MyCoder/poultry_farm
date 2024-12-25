import os
import smtplib

from pyotp import TOTP
# from api.auth.email_config import SMTP_EMAIL,SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
from email.message import EmailMessage
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


async def send_otp_to_user(subject: str, body: str, recipient_email: str):
    try:
        message = EmailMessage()
        message.set_content(body)
        message["subject"] = subject
        message["from"] = SMTP_EMAIL
        message["to"] = recipient_email

        print(SMTP_PORT)
        print(SMTP_EMAIL)
        print(SMTP_PASSWORD)
        print(SMTP_SERVER)

        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))

        with server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)

        return "Message delivered successfully"

    except Exception as e:
        print(e, "👎")
        raise EmailError


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