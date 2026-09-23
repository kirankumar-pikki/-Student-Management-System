# Student Management System

A complete, self-contained **Student Management System** web application
built with **Python, Flask, SQLite, HTML5, CSS3 and JavaScript**. It is
designed as an academic / internship submission project, but is fully
functional and runnable on any machine with Python installed — no paid
services, no external database server, no internet connection required
after installation.

---

## 1. Requirements

- **Python**: 3.9 or newer (tested on Python 3.12)
- **Browser**: any modern browser (Chrome, Edge, Firefox)
- **Packages**: Flask, Werkzeug, pytest — all listed in `requirements.txt`
- **OS**: Windows, macOS, or Linux

No MySQL/PostgreSQL server is required — the app uses **SQLite**, a
file-based database that Python can read/write with no separate
installation, and the database file is created automatically the first
time the app runs.

---

## 2. Installation & Running

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Or simply double-click **`run.bat`**, which creates the virtual
environment, installs dependencies, and starts the server automatically.

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open your browser to:

```
http://127.0.0.1:5000
```

The SQLite database (`instance/students.db`) and a handful of demo
students/courses/attendance/marks records are created automatically on
first launch, so the dashboard is populated immediately.

---

## 3. Demo Login

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

---

## 4. Project Structure

```
Student_Management_System/
│
├── app.py                  # All Flask routes, DB helpers, business logic
├── requirements.txt        # Python dependencies
├── README.md                # This file
├── REFERENCES.md            # Open-source repos used as inspiration
├── PROJECT_DOCUMENTATION.md # Full academic project report
├── .gitignore
├── run.bat                  # One-click Windows launcher
│
├── instance/
│   └── students.db          # SQLite database (auto-created, git-ignored)
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Shared layout: sidebar, topbar, flash messages
│   ├── _flash.html           # Flash message partial
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html         # List + search + pagination
│   ├── student_form.html     # Add / Edit student
│   ├── student_detail.html   # Single student profile (attendance + marks)
│   ├── courses.html
│   ├── course_form.html
│   ├── attendance.html
│   ├── marks.html
│   └── 404.html
│
├── static/
│   ├── css/style.css         # Full custom design system (no external CDN)
│   └── js/app.js             # Sidebar toggle + flash auto-dismiss
│
└── tests/
    └── test_app.py           # 21 pytest tests covering all major features
```

---

## 5. Features

### Authentication
- Session-based login/logout with `werkzeug.security` password hashing
- Every dashboard/data route is protected by a `@login_required` decorator
- Friendly flash-message error handling for bad credentials

### Dashboard
- Total students, courses, attendance records, marks records
- Students grouped by department
- Recently added students
- Quick action buttons (add student, add course, record attendance, enter marks, export CSV)

### Student Management (full CRUD)
- Add / edit / delete / view student profiles
- Fields: roll number, name, email, phone, gender, DOB, department, year,
  semester, address
- Server-side form validation (required fields, valid email, year/semester range)
- Unique constraints on roll number and email, with friendly duplicate errors

### Course Management (full CRUD)
- Course code, name, department, credits
- Add / edit / delete / search

### Attendance Management
- Record total classes and attended classes per student/course
- Automatically computes **Attendance % = attended / total × 100**
- Status badge: **Good** (≥ 75%) or **Warning** (< 75%)
- Rejects attended-classes-greater-than-total as an invalid entry

### Marks / Results Management
- Internal (max 40) + External (max 60) = Total (max 100)
- Automatic grade calculation:
  - 90–100 → A+
  - 80–89 → A
  - 70–79 → B
  - 60–69 → C
  - 50–59 → D
  - Below 50 → F

### Search
- Student search queries the database directly (`WHERE ... LIKE ?`) by
  roll number, name, email, or department — not client-side filtering

### CSV Export
- "Export CSV" button on the Students page and Dashboard downloads all
  student records as a `.csv` file, generated in-memory with Python's
  built-in `csv` module

### REST API
- `GET /api/students` → JSON array of all students
- `GET /api/stats` → JSON dashboard statistics (totals + by-department breakdown)
- Both require an authenticated session (same login as the web UI)

---

## 6. Database Design

SQLite database with five tables, created automatically via
`CREATE TABLE IF NOT EXISTS` on first run:

| Table        | Purpose                                                        |
|--------------|------------------------------------------------------------------|
| `users`      | Admin login accounts (hashed passwords)                        |
| `students`   | Student records (unique roll_no, unique email)                 |
| `courses`    | Course catalog (unique code)                                   |
| `attendance` | One row per (student, course) — total/attended classes         |
| `marks`      | One row per (student, course) — internal/external marks        |

**Relationships**: `attendance` and `marks` each have foreign keys to
`students.id` and `courses.id`, with `ON DELETE CASCADE` so deleting a
student or course cleans up its related records. A `UNIQUE(student_id,
course_id)` constraint on both tables means re-submitting attendance or
marks for the same student+course *updates* the existing record instead
of creating a duplicate.

All queries use **parameterized SQL** (`?` placeholders) — no string
concatenation — to prevent SQL injection.

---

## 7. API Reference

| Method | Endpoint         | Description                                  | Auth required |
|--------|------------------|-----------------------------------------------|----------------|
| GET    | `/api/students`  | Returns all students as a JSON array          | Yes            |
| GET    | `/api/stats`     | Returns dashboard statistics as JSON          | Yes            |

Example:
```bash
curl -c cookies.txt -d "username=admin&password=admin123" http://127.0.0.1:5000/login
curl -b cookies.txt http://127.0.0.1:5000/api/stats
```

---

## 8. Testing

The project includes 21 automated tests covering login, dashboard access,
student CRUD, search, attendance validation, grade calculation, the API
endpoints, CSV export, and the 404 page.

Run them with:

```bash
pip install -r requirements.txt
pytest
```

or for more detail:

```bash
pytest -v
```

All 21 tests pass against this codebase (verified during development —
see the "Testing" section of `PROJECT_DOCUMENTATION.md` for the exact
output).

---

## 9. Uploading to GitHub

```bash
cd Student_Management_System
git init
git add .
git commit -m "Initial commit: Student Management System"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

The included `.gitignore` already excludes the virtual environment, the
SQLite database file, and Python/pytest cache folders, so your repository
stays clean.

---

## 10. Known Limitations

- Single admin role only — no multi-role (teacher/student) login
- No password-reset / "forgot password" flow
- Pagination is basic (page-number links, no infinite scroll)
- Designed for a single SQLite file; not built for concurrent multi-server
  deployment (would need PostgreSQL/MySQL for that scale)
- The Flask development server (`app.run()`) is for local/demo use only —
  a production deployment should use a WSGI server such as Gunicorn behind
  a reverse proxy

---

## 11. License

This project was created for academic/internship submission purposes. See
`REFERENCES.md` for the open-source repositories consulted for inspiration.
