import os
from dotenv import load_dotenv

load_dotenv()

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD","")
SMTP_EMAIL = os.getenv("SMTP_EMAIL","")
SMTP_SERVER = os.getenv("SMTP_SERVER","")
SMTP_PORT = os.getenv("SMTP_PORT",587)

