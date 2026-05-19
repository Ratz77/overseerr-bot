import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OVERSEERR_URL = os.getenv("OVERSEERR_URL", "").rstrip("/")
OVERSEERR_API_KEY = os.getenv("OVERSEERR_API_KEY")
ALLOWED_USERS = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]
POLL_INTERVAL_HOURS = int(os.getenv("POLL_INTERVAL_HOURS", "12"))

WARN_TURKISH    = os.getenv("WARN_TURKISH", "true").lower() == "true"
WARN_LATIN      = os.getenv("WARN_LATIN", "true").lower() == "true"
WARN_TELENOVELA = os.getenv("WARN_TELENOVELA", "true").lower() == "true"
