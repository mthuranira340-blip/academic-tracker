from io import BytesIO

from flask import Blueprint, abort, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from ..extensions import db
from ..forms import ActivityForm, AssistantForm, GradeForm, UnitForm
from ..models import Activity, Grade, ParentStudentLink, Unit, User
from ..services import (
    AI_SUPPORT_PERIOD_MONTHS,
    AI_SUPPORT_PRICE_USD,
    build_activity_payload,
    build_note_library,
    calculate_ai_support_pricing,
    calculate_gpa,
    default_reminder_time,
    filter_notes,
    generate_study_support,
    get_payment_prompt,
    low_grade_alerts,
    performance_timeline,
)


main_bp = Blueprint("main", __name__)


def require_student_role():
    if current_user.is_parent:
        abort(403)


def get_visible_student():
    if current_user.is_student:
        return current_user

    link = ParentStudentLink.query.filter_by(parent_id=current_user.id).first()
    return link.linked_student if link else None


def populate_grade_choices(form):
    students = User.query.filter_by(role="student").order_by(User.username.asc()).all()
    units = Unit.query.order_by(Unit.unit_code.asc()).all()
    form.user_id.choices = [(student.id, f"{student.username} ({student.email})") for student in students]
    form.unit_id.choices = [(unit.id, f"{unit.unit_code} - {unit.unit_name}") for unit in units]


def populate_assistant_choices(form):
    units = Unit.query.order_by(Unit.unit_code.asc()).all()
    form.unit_id.choices = [(unit.id, f"{unit.unit_code} - {unit.unit_name}") for unit in units]


@main_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    selected_student = get_visible_student()
    activity_form = ActivityForm()
    grades = []
    activities = []
    if selected_student:
        grades = (
            Grade.query.filter_by(user_id=selected_student.id)
            .join(Unit)
            .order_by(Grade.academic_year.asc(), Grade.semester.asc())
            .all()
        )
        activities = (
            Activity.query.filter_by(user_id=selected_student.id)
            .order_by(Activity.start_time.asc())
            .all()
        )

    gpa = calculate_gpa(grades)
    timeline_labels, timeline_values = performance_timeline(grades)
    alerts = low_grade_alerts(grades)
    payment_prompt = get_payment_prompt()
    calendar_items, activity_reminders = build_activity_payload(activities)

    summary = {
        "students": User.query.filter_by(role="student").count(),
        "units": Unit.query.count(),
        "grades": Grade.query.count(),
    }

    return render_template(
        "dashboard.html",
        selected_student=selected_student,
        grades=grades,
        gpa=gpa,
        timeline_labels=timeline_labels,
        timeline_values=timeline_values,
        alerts=alerts,
        payment_prompt=payment_prompt,
        activity_form=activity_form,
        calendar_items=calendar_items,
        activity_reminders=activity_reminders,
        summary=summary,
    )


@main_bp.route("/activities", methods=["POST"])
@login_required
def add_activity():
    require_student_role()
    form = ActivityForm()
    if form.validate_on_submit():
        activity = Activity(
            user_id=current_user.id,
            title=form.title.data.strip(),
            category=form.category.data,
            description=form.description.data.strip() if form.description.data else "",
            start_time=form.start_time.data,
            reminder_time=default_reminder_time(form.start_time.data),
        )
        db.session.add(activity)
        db.session.commit()
        flash("Calendar activity added with a 24-hour reminder.", "success")
    else:
        flash("Please complete the activity form correctly before saving.", "danger")

    return redirect(url_for("main.dashboard"))


@main_bp.route("/activities/<int:activity_id>/delete", methods=["POST"])
@login_required
def delete_activity(activity_id):
    require_student_role()
    activity = Activity.query.get_or_404(activity_id)
    if activity.user_id != current_user.id:
        abort(403)

    db.session.delete(activity)
    db.session.commit()
    flash("Activity removed from the calendar.", "info")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/units", methods=["GET", "POST"])
@login_required
def units():
    require_student_role()
    form = UnitForm()
    if form.validate_on_submit():
        unit = Unit(
            unit_name=form.unit_name.data.strip(),
            unit_code=form.unit_code.data.strip().upper(),
            course=form.course.data.strip(),
            level_of_study=form.level_of_study.data,
        )
        db.session.add(unit)
        db.session.commit()
        flash("Unit added successfully.", "success")
        return redirect(url_for("main.units"))

    units_list = Unit.query.order_by(Unit.level_of_study.asc(), Unit.unit_code.asc()).all()
    return render_template("units.html", form=form, units=units_list)


@main_bp.route("/units/<int:unit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_unit(unit_id):
    require_student_role()
    unit = Unit.query.get_or_404(unit_id)
    form = UnitForm(original_code=unit.unit_code, obj=unit)

    if form.validate_on_submit():
        unit.unit_name = form.unit_name.data.strip()
        unit.unit_code = form.unit_code.data.strip().upper()
        unit.course = form.course.data.strip()
        unit.level_of_study = form.level_of_study.data
        db.session.commit()
        flash("Unit updated successfully.", "success")
        return redirect(url_for("main.units"))

    return render_template("edit_unit.html", form=form, unit=unit)


@main_bp.route("/units/<int:unit_id>/delete", methods=["POST"])
@login_required
def delete_unit(unit_id):
    require_student_role()
    unit = Unit.query.get_or_404(unit_id)
    db.session.delete(unit)
    db.session.commit()
    flash("Unit deleted.", "info")
    return redirect(url_for("main.units"))


@main_bp.route("/grades", methods=["GET", "POST"])
@login_required
def grades():
    form = GradeForm()
    populate_grade_choices(form)

    if current_user.is_parent:
        student = get_visible_student()
        grade_list = Grade.query.filter_by(user_id=student.id if student else 0).join(Unit).all()
        return render_template("grades.html", form=None, grades=grade_list, read_only=True)

    if form.validate_on_submit():
        grade = Grade(
            user_id=form.user_id.data,
            unit_id=form.unit_id.data,
            grade=form.grade.data,
            semester=form.semester.data,
            academic_year=form.academic_year.data.strip(),
        )
        db.session.add(grade)
        db.session.commit()
        flash("Grade added successfully.", "success")
        return redirect(url_for("main.grades"))

    grade_list = Grade.query.join(Unit).join(User).order_by(Grade.academic_year.desc(), Grade.semester.desc()).all()
    return render_template("grades.html", form=form, grades=grade_list, read_only=False)


@main_bp.route("/grades/<int:grade_id>/edit", methods=["GET", "POST"])
@login_required
def edit_grade(grade_id):
    require_student_role()
    grade = Grade.query.get_or_404(grade_id)
    form = GradeForm(obj=grade)
    populate_grade_choices(form)

    if form.validate_on_submit():
        grade.user_id = form.user_id.data
        grade.unit_id = form.unit_id.data
        grade.grade = form.grade.data
        grade.semester = form.semester.data
        grade.academic_year = form.academic_year.data.strip()
        db.session.commit()
        flash("Grade updated successfully.", "success")
        return redirect(url_for("main.grades"))

    return render_template("edit_grade.html", form=form, grade=grade)


@main_bp.route("/grades/<int:grade_id>/delete", methods=["POST"])
@login_required
def delete_grade(grade_id):
    require_student_role()
    grade = Grade.query.get_or_404(grade_id)
    db.session.delete(grade)
    db.session.commit()
    flash("Grade deleted.", "info")
    return redirect(url_for("main.grades"))


@main_bp.route("/export/pdf")
@login_required
def export_pdf():
    student = get_visible_student()
    if not student:
        flash("No student profile is linked to this account yet.", "warning")
        return redirect(url_for("main.dashboard"))

    grades = Grade.query.filter_by(user_id=student.id).join(Unit).all()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("University Academic Tracker Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Student: {student.username}", styles["Normal"]),
        Paragraph(f"GPA: {calculate_gpa(grades)}", styles["Normal"]),
        Spacer(1, 12),
    ]

    table_data = [["Unit Code", "Unit Name", "Grade", "Semester", "Academic Year"]]
    for entry in grades:
        table_data.append(
            [entry.unit.unit_code, entry.unit.unit_name, entry.grade, entry.semester, entry.academic_year]
        )

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    content.append(table)

    doc.build(content)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=academic_report.pdf"
    return response


@main_bp.route("/assistant", methods=["GET", "POST"])
@login_required
def assistant():
    form = AssistantForm()
    populate_assistant_choices(form)

    units = Unit.query.order_by(Unit.unit_code.asc()).all()
    selected_unit_id = request.args.get("unit_id", type=int)
    if not selected_unit_id and form.unit_id.choices:
        selected_unit_id = form.unit_id.choices[0][0]

    if request.method == "GET" and selected_unit_id:
        form.unit_id.data = selected_unit_id

    all_notes = build_note_library(units)
    filtered_notes = filter_notes(all_notes, selected_unit_id)
    assistant_response = None
    assistant_source = None
    pricing_amount = calculate_ai_support_pricing()

    if form.validate_on_submit():
        selected_unit = Unit.query.get_or_404(form.unit_id.data)
        assistant_response, used_live_ai, assistant_source = generate_study_support(
            selected_unit, form.assignment_type.data, form.question.data.strip()
        )
        selected_unit_id = selected_unit.id
        filtered_notes = filter_notes(all_notes, selected_unit_id)
        pricing_amount = calculate_ai_support_pricing()
        if used_live_ai:
            flash("AI assistant response generated successfully.", "success")
        else:
            flash("Using the built-in study helper because no live AI key is configured.", "info")

    return render_template(
        "assistant.html",
        form=form,
        notes=filtered_notes,
        selected_unit_id=selected_unit_id,
        pricing_amount=pricing_amount,
        pricing_period_months=AI_SUPPORT_PERIOD_MONTHS,
        pricing_rate=AI_SUPPORT_PRICE_USD,
        assistant_response=assistant_response,
        assistant_source=assistant_source,
    )
