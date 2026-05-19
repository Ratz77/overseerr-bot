import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OVERSEERR_URL = os.getenv("OVERSEERR_URL", "").rstrip("/")
OVERSEERR_API_KEY = os.getenv("OVERSEERR_API_KEY")
ALLOWED_USERS = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]
