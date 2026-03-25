# University Academic Tracker

University Academic Tracker is a beginner-friendly Flask and MySQL web app for managing university units, grades, GPA, progress charts, and parent read-only access.

## Features

- User registration and login for students and parents
- Secure password hashing with Werkzeug
- Role-based access control
- CRUD for units and grades
- GPA calculator
- Progress visualizations using Chart.js
- Parent read-only academic dashboard
- PDF export for academic reports
- Dark mode toggle
- Low-grade notifications

## Project Structure

```text
New project/
|-- app/
|   |-- routes/
|   |   |-- auth.py
|   |   `-- main.py
|   |-- static/
|   |   |-- css/style.css
|   |   `-- js/app.js
|   |-- templates/
|   |-- __init__.py
|   |-- extensions.py
|   |-- forms.py
|   |-- models.py
|   `-- services.py
|-- config.py
|-- requirements.txt
|-- run.py
`-- schema.sql
```

## 1. Install Python Dependencies

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Set Up MySQL

Open MySQL and run:

```sql
SOURCE schema.sql;
```

If `SOURCE schema.sql;` does not work from your current MySQL folder, copy the full path:

```sql
SOURCE C:/Users/Administrator/OneDrive/Pictures/Saved Pictures/Documents/New project/schema.sql;
```

## 3. Configure the Database Connection

Update your MySQL credentials using environment variables before running the app.

Windows PowerShell:

```powershell
$env:SECRET_KEY="replace-this-with-a-secure-secret"
$env:DATABASE_URL="mysql+pymysql://root:your_password@localhost/university_academic_tracker"
```

Optional:

```powershell
$env:LOW_GRADE_THRESHOLD="C"
```

## 4. Run the Application

```powershell
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

## 5. How Roles Work

- `Student`: Can add, edit, and delete units and grades.
- `Parent`: Can only view the linked student's grades, GPA, charts, and PDF report.

When registering a parent account, choose a linked student from the dropdown.

## 6. GPA Logic

The GPA is calculated from the following grade points:

- `A = 4.0`
- `B+ = 3.5`
- `B = 3.0`
- `C+ = 2.5`
- `C = 2.0`
- `D = 1.0`
- `E = 0.0`

## 7. Beginner Notes

- The app uses Flask blueprints to separate authentication and dashboard features.
- SQLAlchemy models represent database tables in Python.
- WTForms handles validation for forms.
- Chart.js renders charts inside the dashboard.
- ReportLab generates the downloadable PDF report.

## 8. Important Tables

Required tables from your specification:

- `users`
- `units`
- `grades`

Additional table used to support parent read-only access:

- `parent_student_links`

## 9. Future Improvements

- Add email notifications for low grades
- Add multiple-child support for parents
- Add semester filters
- Add admin analytics
