from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from .models import Unit, User


GRADE_CHOICES = [
    ("A", "A"),
    ("B+", "B+"),
    ("B", "B"),
    ("C+", "C+"),
    ("C", "C"),
    ("D", "D"),
    ("E", "E"),
]


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    role = SelectField(
        "Role",
        choices=[("student", "Student"), ("parent", "Parent")],
        validators=[DataRequired()],
    )
    linked_student_id = SelectField("Link To Student", coerce=int, choices=[])
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("That email is already registered.")

    def validate_linked_student_id(self, field):
        if self.role.data == "parent" and field.data == 0:
            raise ValidationError("Please link this parent account to a student.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class UnitForm(FlaskForm):
    unit_name = StringField("Unit Name", validators=[DataRequired(), Length(max=120)])
    unit_code = StringField("Unit Code", validators=[DataRequired(), Length(max=30)])
    course = StringField("Course", validators=[DataRequired(), Length(max=120)])
    level_of_study = SelectField(
        "Level of Study",
        choices=[
            ("Year 1", "Year 1"),
            ("Year 2", "Year 2"),
            ("Year 3", "Year 3"),
            ("Year 4", "Year 4"),
            ("Year 5", "Year 5"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Unit")

    def __init__(self, original_code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_code = original_code

    def validate_unit_code(self, field):
        existing = Unit.query.filter_by(unit_code=field.data.upper()).first()
        if existing and field.data.upper() != self.original_code:
            raise ValidationError("That unit code already exists.")


class GradeForm(FlaskForm):
    user_id = SelectField("Student", coerce=int, choices=[], validators=[DataRequired()])
    unit_id = SelectField("Unit", coerce=int, choices=[], validators=[DataRequired()])
    grade = SelectField("Grade", choices=GRADE_CHOICES, validators=[DataRequired()])
    semester = SelectField(
        "Semester",
        choices=[("Semester 1", "Semester 1"), ("Semester 2", "Semester 2"), ("Semester 3", "Semester 3")],
        validators=[DataRequired()],
    )
    academic_year = StringField(
        "Academic Year",
        validators=[DataRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "2025/2026"},
    )
    submit = SubmitField("Save Grade")


class AssistantForm(FlaskForm):
    unit_id = SelectField("Unit", coerce=int, choices=[], validators=[DataRequired()])
    assignment_type = SelectField(
        "Assignment Type",
        choices=[
            ("essay", "Essay"),
            ("research", "Research"),
            ("discussion", "Discussion"),
            ("problem_set", "Problem Set"),
            ("revision", "Revision"),
        ],
        validators=[DataRequired()],
    )
    study_hours = IntegerField("Support Hours", validators=[DataRequired()], default=100)
    question = TextAreaField(
        "What do you need help with?",
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"rows": 6, "placeholder": "Example: Help me outline a networking assignment and give me revision notes."},
    )
    submit = SubmitField("Ask AI Assistant")


class ActivityForm(FlaskForm):
    title = StringField("Activity Title", validators=[DataRequired(), Length(min=3, max=150)])
    category = SelectField(
        "Category",
        choices=[
            ("academic", "Academic Calendar"),
            ("co_curricular", "Co-Curricular Activity"),
        ],
        validators=[DataRequired()],
    )
    start_time = DateTimeLocalField(
        "Activity Date & Time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
        render_kw={"class": "form-control"},
    )
    description = TextAreaField(
        "Description",
        validators=[Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Add details such as venue, agenda, lecturer, or team notes."},
    )
    submit = SubmitField("Save Activity")
