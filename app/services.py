from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import os
from urllib import error, request


GRADE_POINTS = {
    "A": 4.0,
    "B+": 3.5,
    "B": 3.0,
    "C+": 2.5,
    "C": 2.0,
    "D": 1.0,
    "E": 0.0,
}


def grade_to_point(grade):
    return GRADE_POINTS.get(grade, 0.0)


def calculate_gpa(grades):
    if not grades:
        return 0.0

    total_points = sum(grade_to_point(entry.grade) for entry in grades)
    return round(total_points / len(grades), 2)


def performance_timeline(grades):
    grouped = defaultdict(list)
    for entry in grades:
        label = f"{entry.academic_year} - {entry.semester}"
        grouped[label].append(grade_to_point(entry.grade))

    labels = list(grouped.keys())
    averages = [round(sum(values) / len(values), 2) for values in grouped.values()]
    return labels, averages


def low_grade_alerts(grades):
    return [entry for entry in grades if grade_to_point(entry.grade) <= 2.0]


ACADEMIC_CALENDAR = [
    {
        "name": "Semester 1",
        "start": (1, 8),
        "end": (4, 30),
        "payment_deadline": (1, 31),
        "services": [
            {"name": "Tuition", "amount_usd": 350},
            {"name": "Registration", "amount_usd": 40},
            {"name": "Library", "amount_usd": 25},
            {"name": "Student Portal", "amount_usd": 15},
        ],
    },
    {
        "name": "Semester 2",
        "start": (5, 1),
        "end": (8, 31),
        "payment_deadline": (5, 31),
        "services": [
            {"name": "Tuition", "amount_usd": 350},
            {"name": "Examination", "amount_usd": 60},
            {"name": "Lab Access", "amount_usd": 45},
            {"name": "Hostel Support", "amount_usd": 120},
        ],
    },
    {
        "name": "Semester 3",
        "start": (9, 1),
        "end": (12, 20),
        "payment_deadline": (9, 30),
        "services": [
            {"name": "Tuition", "amount_usd": 350},
            {"name": "Project Supervision", "amount_usd": 80},
            {"name": "Internet Access", "amount_usd": 20},
            {"name": "E-Learning", "amount_usd": 30},
        ],
    },
]

PAYPAL_ACCOUNT = "mthuranira340@gmail.com"
AI_SUPPORT_PRICE_USD = 30
AI_SUPPORT_PERIOD_MONTHS = 4


def get_payment_prompt(today=None):
    today = today or date.today()

    for term in ACADEMIC_CALENDAR:
        start = date(today.year, term["start"][0], term["start"][1])
        end = date(today.year, term["end"][0], term["end"][1])
        deadline = date(today.year, term["payment_deadline"][0], term["payment_deadline"][1])
        service_names = [service["name"] for service in term["services"]]
        total_amount = sum(service["amount_usd"] for service in term["services"])

        if start <= today <= end:
            days_left = (deadline - today).days
            if days_left >= 0:
                status = "Payment window is open"
                tone = "warning" if days_left <= 7 else "primary"
                summary = (
                    f"Please pay for {', '.join(service_names)} before "
                    f"{deadline.strftime('%d %b %Y')} to keep your services active."
                )
            else:
                status = "Payment deadline has passed"
                tone = "danger"
                summary = (
                    f"Payment for {', '.join(service_names)} was due on "
                    f"{deadline.strftime('%d %b %Y')}. Clear the balance to restore uninterrupted access."
                )

            return {
                "term_name": term["name"],
                "status": status,
                "tone": tone,
                "deadline": deadline.strftime("%d %b %Y"),
                "days_left": days_left,
                "services": term["services"],
                "total_amount_usd": total_amount,
                "paypal_account": PAYPAL_ACCOUNT,
                "summary": summary,
            }

    next_term = ACADEMIC_CALENDAR[0]
    next_deadline = date(today.year + 1, next_term["payment_deadline"][0], next_term["payment_deadline"][1])
    next_total_amount = sum(service["amount_usd"] for service in next_term["services"])
    return {
        "term_name": next_term["name"],
        "status": "Upcoming payment cycle",
        "tone": "info",
        "deadline": next_deadline.strftime("%d %b %Y"),
        "days_left": (next_deadline - today).days,
        "services": next_term["services"],
        "total_amount_usd": next_total_amount,
        "paypal_account": PAYPAL_ACCOUNT,
        "summary": (
            f"The next academic payment cycle is for {next_term['name']}. "
            f"Plan ahead for {', '.join(service['name'] for service in next_term['services'])} "
            f"before {next_deadline.strftime('%d %b %Y')}."
        ),
    }


def calculate_ai_support_pricing():
    return AI_SUPPORT_PRICE_USD


def build_note_library(units):
    notes = []
    for unit in units:
        notes.extend(
            [
                {
                    "unit_id": unit.id,
                    "unit_code": unit.unit_code,
                    "unit_name": unit.unit_name,
                    "title": f"{unit.unit_name} Core Concepts",
                    "tag": "Best Notes",
                    "quality_score": 98,
                    "summary": (
                        f"High-yield notes for {unit.unit_code} covering definitions, core principles, and exam-ready explanations."
                    ),
                    "points": [
                        f"Start with the main learning outcomes for {unit.unit_name}.",
                        f"Break each topic into short definitions, worked examples, and likely exam questions.",
                        f"Review course-specific vocabulary and lecturer emphasis areas each week.",
                    ],
                },
                {
                    "unit_id": unit.id,
                    "unit_code": unit.unit_code,
                    "unit_name": unit.unit_name,
                    "title": f"{unit.unit_name} Assignment Guide",
                    "tag": "Assignment Support",
                    "quality_score": 91,
                    "summary": (
                        f"A structured guide for handling assignments in {unit.unit_code} with planning, references, and submission tips."
                    ),
                    "points": [
                        "Read the rubric first and turn it into a checklist.",
                        "Collect lecturer notes, class examples, and recommended readings before drafting.",
                        "Reserve time for editing, citations, and final proof-reading.",
                    ],
                },
            ]
        )

    return sorted(notes, key=lambda item: (-item["quality_score"], item["unit_code"]))


def filter_notes(notes, unit_id=None):
    if not unit_id:
        return notes
    return [note for note in notes if note["unit_id"] == unit_id]


def generate_study_support(unit, assignment_type, question):
    api_key = os.environ.get("OPENAI_API_KEY")
    fallback = (
        f"Study support for {unit.unit_code} - {unit.unit_name}\n\n"
        f"Assignment type: {assignment_type.replace('_', ' ').title()}\n"
        f"Request: {question}\n\n"
        "Suggested approach:\n"
        "1. Restate the question in your own words and identify the required output.\n"
        "2. Split the work into introduction, key discussion points, evidence/examples, and conclusion.\n"
        "3. Use your lecture notes, unit readings, and class examples to support each section.\n"
        "4. Draft one strong argument at a time, then review for clarity, citations, and accuracy.\n\n"
        "Quick notes:\n"
        f"- Focus on the main concepts repeatedly covered in {unit.unit_name}.\n"
        "- Add one practical example or case study for each major point.\n"
        "- Finish with a short revision summary before submitting."
    )

    if not api_key:
        return fallback, False, "Offline study helper"

    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": (
            "You are a university study assistant. Help a student complete an assignment and provide concise course notes.\n"
            f"Unit: {unit.unit_code} - {unit.unit_name}\n"
            f"Course: {unit.course}\n"
            f"Level: {unit.level_of_study}\n"
            f"Assignment type: {assignment_type}\n"
            f"Student request: {question}\n\n"
            "Return:\n"
            "1. A short assignment plan\n"
            "2. Key notes for the unit\n"
            "3. Practical tips for scoring well"
        ),
    }

    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            output_text = body.get("output_text")
            if output_text:
                return output_text, True, payload["model"]
    except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
        pass

    return fallback, False, "Offline study helper"


def build_activity_payload(activities, now=None):
    now = now or datetime.now()
    calendar_items = []
    reminders = []

    for activity in activities:
        hours_until = round((activity.start_time - now).total_seconds() / 3600, 1)
        reminder_due = activity.reminder_time <= now < activity.start_time

        item = {
            "id": activity.id,
            "title": activity.title,
            "category": activity.category,
            "description": activity.description or "No extra details added.",
            "date_label": activity.start_time.strftime("%d %b %Y"),
            "time_label": activity.start_time.strftime("%H:%M"),
            "reminder_label": activity.reminder_time.strftime("%d %b %Y %H:%M"),
            "hours_until": hours_until,
            "is_upcoming": activity.start_time >= now,
        }
        calendar_items.append(item)

        if reminder_due:
            reminders.append(
                {
                    "title": activity.title,
                    "category": activity.category.replace("_", " ").title(),
                    "start_label": activity.start_time.strftime("%d %b %Y at %H:%M"),
                    "message": (
                        f"Reminder: {activity.title} is scheduled for {activity.start_time.strftime('%d %b %Y at %H:%M')}."
                    ),
                }
            )

    calendar_items.sort(key=lambda item: (not item["is_upcoming"], item["date_label"], item["time_label"]))
    reminders.sort(key=lambda item: item["start_label"])
    return calendar_items, reminders


def default_reminder_time(start_time):
    return start_time - timedelta(hours=24)
