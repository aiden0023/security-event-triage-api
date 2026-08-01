import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # Required settings needed before the app is able to start
    REQUIRED_SETTINGS = ("SECRET_KEY", "JWT_SECRET_KEY", "SQLALCHEMY_DATABASE_URI")

    # --- Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # --- SQLAlchemy ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}

    # --- Auth ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)

    # --- Rate Limiting ---
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # --- API Behavior ---
    # DEFAULT_PAGE_SIZE should always stay well below the MAX_PAGE_SIZE
    DEFAULT_PAGE_SIZE = 25
    # Recommended to not increase MAX_PAGE_SIZE; higher size will cause larger responses
    MAX_PAGE_SIZE = 100
    # MAX_DESCRIPTION_LENGTH basically caps Postgres's TEXT
    MAX_DESCRIPTION_LENGTH = 4000
    # MAX_CONTENT_LENGTH caps request bodies (1 MB)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024


class DevConfig(BaseConfig):
    DEBUG = True
    # Flip SQLALCHEMY_ECHO to True in order to watch the SQL being emitted
    SQLALCHEMY_ECHO = False


class TestConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = secrets.token_urlsafe(32)
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/triage_test"
    )
    # Off by default so unrelated tests do not trip limits. Rate-limit test re-enables this in
    # a separate app
    RATELIMIT_ENABLED = False


class ProdConfig(BaseConfig):
    DEBUG = False


config_by_name = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
