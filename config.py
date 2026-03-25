import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost/university_academic_tracker",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_GRADE_THRESHOLD = os.environ.get("LOW_GRADE_THRESHOLD", "C")

