import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY is missing. Add it to your .env file."
    )

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# PostgreSQL defaults (containerized docker-compose service)
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ai_agency")
DB_USER = os.getenv("DB_USER", "ai_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ai_secure_password")

# DSN for psycopg/psycopg2 connections
DB_DSN = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)