from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class ParentStudentLink(db.Model):
    __tablename__ = "parent_student_links"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    grades = db.relationship("Grade", backref="student", lazy=True, cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="owner", lazy=True, cascade="all, delete-orphan")
    parent_links = db.relationship(
        "ParentStudentLink",
        foreign_keys=[ParentStudentLink.parent_id],
        backref="parent",
        lazy=True,
        cascade="all, delete-orphan",
    )
    student_links = db.relationship(
        "ParentStudentLink",
        foreign_keys=[ParentStudentLink.student_id],
        backref="linked_student",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    @property
    def is_parent(self):
        return self.role == "parent"

    @property
    def is_student(self):
        return self.role == "student"


class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True)
    unit_name = db.Column(db.String(120), nullable=False)
    unit_code = db.Column(db.String(30), unique=True, nullable=False)
    course = db.Column(db.String(120), nullable=False)
    level_of_study = db.Column(db.String(50), nullable=False)

    grades = db.relationship("Grade", backref="unit", lazy=True, cascade="all, delete-orphan")


class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    grade = db.Column(db.String(2), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reminder_time = db.Column(db.DateTime, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
