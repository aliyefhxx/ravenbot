"""Mərkəzi konfiqurasiya"""
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")  # şifrələnmiş və ya açıq
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    CMD_PREFIX = os.getenv("CMD_PREFIX", ".")
    LOG_TO_SAVED = os.getenv("LOG_TO_SAVED", "1") == "1"
