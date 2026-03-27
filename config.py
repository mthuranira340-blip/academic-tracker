import os


def resolve_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    # Default to SQLite so the app can run on free/demo hosting without MySQL.
    return "sqlite:///academic_tracker_demo.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_GRADE_THRESHOLD = os.environ.get("LOW_GRADE_THRESHOLD", "C")
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    REMEMBER_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
