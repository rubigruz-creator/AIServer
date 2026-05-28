import os

DB_PATH = os.getenv("INTAKE_DB_PATH", "/data/intake.db")
ADMIN_USER = os.getenv("INTAKE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("INTAKE_ADMIN_PASSWORD", "")
WEBHOOK_URL = os.getenv("INTAKE_WEBHOOK_URL", "").strip()
TZ = os.getenv("TZ", "Europe/Moscow")
