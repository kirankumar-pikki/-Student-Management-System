"""
Student Management System
A Flask + SQLite web application for managing students, courses,
attendance and marks in a small college/department setting.

Run:
    python app.py
Then open http://127.0.0.1:5000  (demo login: admin / admin123)
"""

import os
import io
import csv
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, g, render_template, request, redirect, url_for,
    session, flash, jsonify, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE = os.path.join(INSTANCE_DIR, "students.db")

os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__)
# In a real deployment this MUST come from an environment variable.
app.config["SECRET_KEY"] = os.environ.get("SMS_SECRET_KEY", "dev-secret-key-change-me")
app.config["DATABASE"] = DATABASE

DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "MCA", "MBA", "IT"]
YEARS = [1, 2, 3, 4]
SEMESTERS = [1, 2]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Open a new database connection for this request if one doesn't exist."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables (if missing) and seed demo data on first run."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            gender TEXT,
            dob TEXT,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            address TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            total_classes INTEGER NOT NULL,
            attended_classes INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
            UNIQUE (student_id, course_id)
        );

        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            internal INTEGER NOT NULL,
            external INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
            UNIQUE (student_id, course_id)
        );
        """
    )
    db.commit()

    # Seed a demo admin account
    admin = db.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if admin is None:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )
        db.commit()

    # Seed demo data only if the students table is empty
    count = db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    if count == 0:
        seed_demo_data(db)


def seed_demo_data(db):
    courses = [
        ("CS101", "Programming Fundamentals", "CSE", 4),
        ("CS201", "Data Structures", "CSE", 4),
        ("CS301", "Database Management Systems", "CSE", 3),
        ("MCA501", "Full Stack Web Development", "MCA", 4),
        ("MCA502", "Operating Systems", "MCA", 3),
        ("EC101", "Basic Electronics", "ECE", 3),
    ]
    db.executemany(
        "INSERT INTO courses (code, name, department, credits) VALUES (?, ?, ?, ?)",
        courses,
    )

    students = [
        ("MCA24001", "Ananya Rao", "ananya.rao@example.com", "9876543210", "Female", "2003-05-12", "MCA", 2, 1, "Vijayawada, AP"),
        ("MCA24002", "Ravi Teja", "ravi.teja@example.com", "9876543211", "Male", "2002-11-03", "MCA", 2, 1, "Guntur, AP"),
        ("CSE23010", "Priya Sharma", "priya.sharma@example.com", "9876543212", "Female", "2003-02-20", "CSE", 3, 1, "Hyderabad, TS"),
        ("CSE23011", "Karthik Reddy", "karthik.reddy@example.com", "9876543213", "Male", "2003-07-15", "CSE", 3, 1, "Vizag, AP"),
        ("ECE22005", "Sneha Patel", "sneha.patel@example.com", "9876543214", "Female", "2002-09-09", "ECE", 4, 1, "Rajahmundry, AP"),
    ]
    db.executemany(
        """INSERT INTO students
           (roll_no, name, email, phone, gender, dob, department, year, semester, address)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        students,
    )
    db.commit()

    student_ids = [r["id"] for r in db.execute("SELECT id FROM students ORDER BY id").fetchall()]
    course_ids = [r["id"] for r in db.execute("SELECT id FROM courses ORDER BY id").fetchall()]

    attendance_rows = []
    marks_rows = []
    import random
    random.seed(42)
    for sid in student_ids:
        for cid in random.sample(course_ids, k=min(3, len(course_ids))):
            total = random.choice([40, 45, 50, 60])
            attended = random.randint(int(total * 0.55), total)
            attendance_rows.append((sid, cid, total, attended))
            internal = random.randint(20, 40)
            external = random.randint(25, 60)
            marks_rows.append((sid, cid, internal, external))

    db.executemany(
        """INSERT OR IGNORE INTO attendance (student_id, course_id, total_classes, attended_classes)
           VALUES (?, ?, ?, ?)""",
        attendance_rows,
    )
    db.executemany(
        """INSERT OR IGNORE INTO marks (student_id, course_id, internal, external)
           VALUES (?, ?, ?, ?)""",
        marks_rows,
    )
    db.commit()


@app.cli.command("init-db")
def init_db_command():
    """CLI: `flask --app app.py init-db` to (re)initialize the database."""
    init_db()
    print("Database initialized.")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


@app.context_processor
def inject_user():
    return {"current_user": session.get("username")}


# ---------------------------------------------------------------------------
# Domain helpers (grading / attendance calculations)
# ---------------------------------------------------------------------------

def compute_grade(total_marks):
    if total_marks >= 90:
        return "A+"
    if total_marks >= 80:
        return "A"
    if total_marks >= 70:
        return "B"
    if total_marks >= 60:
        return "C"
    if total_marks >= 50:
        return "D"
    return "F"


def attendance_status(percentage):
    return "Good" if percentage >= 75 else "Warning"


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error = None

        if not username or not password:
            error = "Please enter both username and password."
        else:
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid username or password."

        if error:
            flash(error, "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    total_courses = db.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
    total_attendance = db.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()["c"]
    total_marks = db.execute("SELECT COUNT(*) AS c FROM marks").fetchone()["c"]

    by_department = db.execute(
        """SELECT department, COUNT(*) AS c
           FROM students GROUP BY department ORDER BY c DESC"""
    ).fetchall()

    recent_students = db.execute(
        """SELECT * FROM students ORDER BY id DESC LIMIT 5"""
    ).fetchall()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_courses=total_courses,
        total_attendance=total_attendance,
        total_marks=total_marks,
        by_department=by_department,
        recent_students=recent_students,
    )


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------

@app.route("/students")
@login_required
def students():
    db = get_db()
    q = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    page = max(int(request.args.get("page", 1) or 1), 1)
    per_page = 8

    where = []
    params = []
    if q:
        where.append("(roll_no LIKE ? OR name LIKE ? OR email LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    if department:
        where.append("department = ?")
        params.append(department)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total = db.execute(
        f"SELECT COUNT(*) AS c FROM students {where_sql}", params
    ).fetchone()["c"]
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    rows = db.execute(
        f"""SELECT * FROM students {where_sql}
            ORDER BY id DESC LIMIT ? OFFSET ?""",
        params + [per_page, offset],
    ).fetchall()

    return render_template(
        "students.html",
        students=rows,
        q=q,
        department=department,
        departments=DEPARTMENTS,
        page=page,
        total_pages=total_pages,
        total=total,
    )


def _student_form_data():
    return {
        "roll_no": request.form.get("roll_no", "").strip(),
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "gender": request.form.get("gender", "").strip(),
        "dob": request.form.get("dob", "").strip(),
        "department": request.form.get("department", "").strip(),
        "year": request.form.get("year", "").strip(),
        "semester": request.form.get("semester", "").strip(),
        "address": request.form.get("address", "").strip(),
    }


def _validate_student(data):
    errors = []
    if not data["roll_no"]:
        errors.append("Roll number is required.")
    if not data["name"]:
        errors.append("Full name is required.")
    if not data["email"] or "@" not in data["email"]:
        errors.append("A valid email is required.")
    if not data["department"]:
        errors.append("Department is required.")
    if data["year"] not in [str(y) for y in YEARS]:
        errors.append("Year must be between 1 and 4.")
    if data["semester"] not in [str(s) for s in SEMESTERS]:
        errors.append("Semester must be 1 or 2.")
    return errors


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        data = _student_form_data()
        errors = _validate_student(data)

        db = get_db()
        if not errors:
            try:
                db.execute(
                    """INSERT INTO students
                       (roll_no, name, email, phone, gender, dob, department, year, semester, address)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["roll_no"], data["name"], data["email"], data["phone"],
                        data["gender"], data["dob"], data["department"],
                        int(data["year"]), int(data["semester"]), data["address"],
                    ),
                )
                db.commit()
                flash("Student added successfully.", "success")
                return redirect(url_for("students"))
            except sqlite3.IntegrityError:
                errors.append("A student with that roll number or email already exists.")

        for e in errors:
            flash(e, "danger")
        return render_template(
            "student_form.html", student=data, mode="add",
            departments=DEPARTMENTS, years=YEARS, semesters=SEMESTERS,
        )

    return render_template(
        "student_form.html", student=None, mode="add",
        departments=DEPARTMENTS, years=YEARS, semesters=SEMESTERS,
    )


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    db = get_db()
    existing = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if existing is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        data = _student_form_data()
        errors = _validate_student(data)

        if not errors:
            try:
                db.execute(
                    """UPDATE students SET
                       roll_no=?, name=?, email=?, phone=?, gender=?, dob=?,
                       department=?, year=?, semester=?, address=?
                       WHERE id=?""",
                    (
                        data["roll_no"], data["name"], data["email"], data["phone"],
                        data["gender"], data["dob"], data["department"],
                        int(data["year"]), int(data["semester"]), data["address"],
                        student_id,
                    ),
                )
                db.commit()
                flash("Student updated successfully.", "success")
                return redirect(url_for("students"))
            except sqlite3.IntegrityError:
                errors.append("A student with that roll number or email already exists.")

        for e in errors:
            flash(e, "danger")
        data["id"] = student_id
        return render_template(
            "student_form.html", student=data, mode="edit",
            departments=DEPARTMENTS, years=YEARS, semesters=SEMESTERS,
        )

    return render_template(
        "student_form.html", student=existing, mode="edit",
        departments=DEPARTMENTS, years=YEARS, semesters=SEMESTERS,
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    flash("Student deleted.", "info")
    return redirect(url_for("students"))


@app.route("/students/<int:student_id>")
@login_required
def view_student(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    attendance_rows = db.execute(
        """SELECT a.*, c.name AS course_name, c.code AS course_code
           FROM attendance a JOIN courses c ON a.course_id = c.id
           WHERE a.student_id = ?""",
        (student_id,),
    ).fetchall()

    marks_rows = db.execute(
        """SELECT m.*, c.name AS course_name, c.code AS course_code
           FROM marks m JOIN courses c ON m.course_id = c.id
           WHERE m.student_id = ?""",
        (student_id,),
    ).fetchall()

    attendance_view = []
    for a in attendance_rows:
        pct = round((a["attended_classes"] / a["total_classes"]) * 100, 1) if a["total_classes"] else 0
        attendance_view.append({**dict(a), "percentage": pct, "status": attendance_status(pct)})

    marks_view = []
    for m in marks_rows:
        total = m["internal"] + m["external"]
        marks_view.append({**dict(m), "total": total, "grade": compute_grade(total)})

    return render_template(
        "student_detail.html",
        student=student, attendance_view=attendance_view, marks_view=marks_view,
    )


# ---------------------------------------------------------------------------
# Course CRUD
# ---------------------------------------------------------------------------

@app.route("/courses", methods=["GET", "POST"])
@login_required
def courses():
    db = get_db()

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        credits = request.form.get("credits", "").strip()

        errors = []
        if not code:
            errors.append("Course code is required.")
        if not name:
            errors.append("Course name is required.")
        if not department:
            errors.append("Department is required.")
        if not credits.isdigit() or not (1 <= int(credits) <= 10):
            errors.append("Credits must be a number between 1 and 10.")

        if not errors:
            try:
                db.execute(
                    "INSERT INTO courses (code, name, department, credits) VALUES (?, ?, ?, ?)",
                    (code, name, department, int(credits)),
                )
                db.commit()
                flash("Course added successfully.", "success")
                return redirect(url_for("courses"))
            except sqlite3.IntegrityError:
                errors.append("A course with that code already exists.")

        for e in errors:
            flash(e, "danger")

    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute(
            """SELECT * FROM courses
               WHERE code LIKE ? OR name LIKE ? OR department LIKE ?
               ORDER BY id DESC""",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()

    return render_template("courses.html", courses=rows, q=q, departments=DEPARTMENTS)


@app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    db = get_db()
    existing = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if existing is None:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        credits = request.form.get("credits", "").strip()

        errors = []
        if not code:
            errors.append("Course code is required.")
        if not name:
            errors.append("Course name is required.")
        if not department:
            errors.append("Department is required.")
        if not credits.isdigit() or not (1 <= int(credits) <= 10):
            errors.append("Credits must be a number between 1 and 10.")

        if not errors:
            try:
                db.execute(
                    "UPDATE courses SET code=?, name=?, department=?, credits=? WHERE id=?",
                    (code, name, department, int(credits), course_id),
                )
                db.commit()
                flash("Course updated.", "success")
                return redirect(url_for("courses"))
            except sqlite3.IntegrityError:
                errors.append("A course with that code already exists.")

        for e in errors:
            flash(e, "danger")
        form_data = {"id": course_id, "code": code, "name": name, "department": department, "credits": credits}
        return render_template("course_form.html", course=form_data, departments=DEPARTMENTS)

    return render_template("course_form.html", course=existing, departments=DEPARTMENTS)


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    db.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("courses"))


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    db = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", "")
        course_id = request.form.get("course_id", "")
        total_classes = request.form.get("total_classes", "")
        attended_classes = request.form.get("attended_classes", "")

        errors = []
        if not (student_id.isdigit() and course_id.isdigit()):
            errors.append("Please select a valid student and course.")
        if not total_classes.isdigit() or int(total_classes) <= 0:
            errors.append("Total classes must be a positive number.")
        if not attended_classes.isdigit():
            errors.append("Attended classes must be a number.")
        if not errors and int(attended_classes) > int(total_classes):
            errors.append("Attended classes cannot be greater than total classes.")

        if not errors:
            try:
                db.execute(
                    """INSERT INTO attendance (student_id, course_id, total_classes, attended_classes)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(student_id, course_id) DO UPDATE SET
                         total_classes = excluded.total_classes,
                         attended_classes = excluded.attended_classes""",
                    (int(student_id), int(course_id), int(total_classes), int(attended_classes)),
                )
                db.commit()
                flash("Attendance recorded.", "success")
                return redirect(url_for("attendance"))
            except sqlite3.IntegrityError as exc:
                errors.append(f"Could not save attendance ({exc}).")

        for e in errors:
            flash(e, "danger")

    rows = db.execute(
        """SELECT a.*, s.name AS student_name, s.roll_no, c.name AS course_name, c.code AS course_code
           FROM attendance a
           JOIN students s ON a.student_id = s.id
           JOIN courses c ON a.course_id = c.id
           ORDER BY a.id DESC"""
    ).fetchall()

    records = []
    for r in rows:
        pct = round((r["attended_classes"] / r["total_classes"]) * 100, 1) if r["total_classes"] else 0
        records.append({**dict(r), "percentage": pct, "status": attendance_status(pct)})

    all_students = db.execute("SELECT id, roll_no, name FROM students ORDER BY name").fetchall()
    all_courses = db.execute("SELECT id, code, name FROM courses ORDER BY name").fetchall()

    return render_template(
        "attendance.html", records=records,
        all_students=all_students, all_courses=all_courses,
    )


@app.route("/attendance/<int:record_id>/delete", methods=["POST"])
@login_required
def delete_attendance(record_id):
    db = get_db()
    db.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
    db.commit()
    flash("Attendance record deleted.", "info")
    return redirect(url_for("attendance"))


# ---------------------------------------------------------------------------
# Marks / Results
# ---------------------------------------------------------------------------

@app.route("/marks", methods=["GET", "POST"])
@login_required
def marks():
    db = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", "")
        course_id = request.form.get("course_id", "")
        internal = request.form.get("internal", "")
        external = request.form.get("external", "")

        errors = []
        if not (student_id.isdigit() and course_id.isdigit()):
            errors.append("Please select a valid student and course.")
        if not internal.isdigit() or not (0 <= int(internal) <= 40):
            errors.append("Internal marks must be between 0 and 40.")
        if not external.isdigit() or not (0 <= int(external) <= 60):
            errors.append("External marks must be between 0 and 60.")

        if not errors:
            try:
                db.execute(
                    """INSERT INTO marks (student_id, course_id, internal, external)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(student_id, course_id) DO UPDATE SET
                         internal = excluded.internal,
                         external = excluded.external""",
                    (int(student_id), int(course_id), int(internal), int(external)),
                )
                db.commit()
                flash("Marks recorded.", "success")
                return redirect(url_for("marks"))
            except sqlite3.IntegrityError as exc:
                errors.append(f"Could not save marks ({exc}).")

        for e in errors:
            flash(e, "danger")

    rows = db.execute(
        """SELECT m.*, s.name AS student_name, s.roll_no, c.name AS course_name, c.code AS course_code
           FROM marks m
           JOIN students s ON m.student_id = s.id
           JOIN courses c ON m.course_id = c.id
           ORDER BY m.id DESC"""
    ).fetchall()

    records = []
    for r in rows:
        total = r["internal"] + r["external"]
        records.append({**dict(r), "total": total, "grade": compute_grade(total)})

    all_students = db.execute("SELECT id, roll_no, name FROM students ORDER BY name").fetchall()
    all_courses = db.execute("SELECT id, code, name FROM courses ORDER BY name").fetchall()

    return render_template(
        "marks.html", records=records,
        all_students=all_students, all_courses=all_courses,
    )


@app.route("/marks/<int:record_id>/delete", methods=["POST"])
@login_required
def delete_marks(record_id):
    db = get_db()
    db.execute("DELETE FROM marks WHERE id = ?", (record_id,))
    db.commit()
    flash("Marks record deleted.", "info")
    return redirect(url_for("marks"))


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

@app.route("/students/export")
@login_required
def export_students():
    db = get_db()
    rows = db.execute("SELECT * FROM students ORDER BY id").fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Roll No", "Name", "Email", "Phone", "Gender", "DOB",
        "Department", "Year", "Semester", "Address",
    ])
    for s in rows:
        writer.writerow([
            s["roll_no"], s["name"], s["email"], s["phone"], s["gender"], s["dob"],
            s["department"], s["year"], s["semester"], s["address"],
        ])

    csv_data = output.getvalue()
    filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.route("/api/students")
@login_required
def api_students():
    db = get_db()
    rows = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    stats = {
        "total_students": db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"],
        "total_courses": db.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"],
        "total_attendance_records": db.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()["c"],
        "total_marks_records": db.execute("SELECT COUNT(*) AS c FROM marks").fetchone()["c"],
        "students_by_department": {
            r["department"]: r["c"]
            for r in db.execute(
                "SELECT department, COUNT(*) AS c FROM students GROUP BY department"
            ).fetchall()
        },
    }
    return jsonify(stats)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
