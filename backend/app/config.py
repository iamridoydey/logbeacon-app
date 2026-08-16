import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")
    REDIS_URL = os.environ.get("REDIS_URL")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL = os.environ.get("GROQ_MODEL")
    LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", 7))
    MAX_ERROR_LENGTH = int(os.environ.get("MAX_ERROR_LENGTH", 500))
    PRICE_PER_MILLION_TOKENS = float(os.environ.get("PRICE_PER_MILLION_TOKENS", 0.05))