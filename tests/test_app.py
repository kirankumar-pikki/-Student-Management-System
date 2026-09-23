"""
Automated tests for the Student Management System.

Run with:
    pytest
from the project root (with the virtual environment activated).
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app_module.app.config["DATABASE"] = db_path
    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = False

    with app_module.app.app_context():
        app_module.init_db()

    with app_module.app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def login(client, username="admin", password="admin123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def test_database_initializes_with_demo_data(client):
    with app_module.app.app_context():
        db = app_module.get_db()
        user_count = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        student_count = db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
        course_count = db.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
    assert user_count == 1
    assert student_count > 0
    assert course_count > 0


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Sign In" in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_with_wrong_password_fails(client):
    resp = login(client, "admin", "wrongpassword")
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_login_with_correct_credentials_succeeds(client):
    resp = login(client)
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data


def test_logout_clears_session(client):
    login(client)
    client.get("/logout")
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def test_dashboard_shows_stats_after_login(client):
    login(client)
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Total Students" in resp.data
    assert b"Total Courses" in resp.data


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------

def test_student_listing(client):
    login(client)
    resp = client.get("/students")
    assert resp.status_code == 200
    assert b"Roll No" in resp.data


def test_add_student_success(client):
    login(client)
    resp = client.post(
        "/students/add",
        data={
            "roll_no": "PYTEST001",
            "name": "Pytest Student",
            "email": "pytest.student@example.com",
            "phone": "9000000000",
            "gender": "Female",
            "dob": "2003-04-01",
            "department": "MCA",
            "year": "2",
            "semester": "1",
            "address": "Test Lane",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Pytest Student" in resp.data


def test_add_student_missing_required_field_fails(client):
    login(client)
    resp = client.post(
        "/students/add",
        data={
            "roll_no": "",
            "name": "No Roll",
            "email": "noroll@example.com",
            "department": "MCA",
            "year": "1",
            "semester": "1",
        },
        follow_redirects=True,
    )
    assert b"Roll number is required" in resp.data


def test_add_student_duplicate_email_rejected(client):
    login(client)
    payload = {
        "roll_no": "DUP001",
        "name": "Dup One",
        "email": "dup.test@example.com",
        "phone": "1",
        "gender": "Male",
        "dob": "2000-01-01",
        "department": "MCA",
        "year": "1",
        "semester": "1",
        "address": "",
    }
    client.post("/students/add", data=payload, follow_redirects=True)
    payload["roll_no"] = "DUP002"
    resp = client.post("/students/add", data=payload, follow_redirects=True)
    assert b"already exists" in resp.data


def test_student_search(client):
    login(client)
    client.post(
        "/students/add",
        data={
            "roll_no": "SEARCHME",
            "name": "Findable Student",
            "email": "findable@example.com",
            "phone": "1",
            "gender": "Male",
            "dob": "2000-01-01",
            "department": "MCA",
            "year": "1",
            "semester": "1",
            "address": "",
        },
        follow_redirects=True,
    )
    resp = client.get("/students?q=Findable")
    assert b"Findable Student" in resp.data


def test_edit_and_delete_student(client):
    login(client)
    client.post(
        "/students/add",
        data={
            "roll_no": "EDIT001",
            "name": "Before Edit",
            "email": "beforeedit@example.com",
            "phone": "1",
            "gender": "Male",
            "dob": "2000-01-01",
            "department": "MCA",
            "year": "1",
            "semester": "1",
            "address": "",
        },
        follow_redirects=True,
    )
    with app_module.app.app_context():
        db = app_module.get_db()
        student = db.execute("SELECT id FROM students WHERE roll_no='EDIT001'").fetchone()
        sid = student["id"]

    resp = client.post(
        f"/students/{sid}/edit",
        data={
            "roll_no": "EDIT001",
            "name": "After Edit",
            "email": "beforeedit@example.com",
            "phone": "1",
            "gender": "Male",
            "dob": "2000-01-01",
            "department": "MCA",
            "year": "1",
            "semester": "1",
            "address": "",
        },
        follow_redirects=True,
    )
    assert b"After Edit" in resp.data

    resp = client.post(f"/students/{sid}/delete", follow_redirects=True)
    assert b"deleted" in resp.data.lower()


# ---------------------------------------------------------------------------
# Attendance validation
# ---------------------------------------------------------------------------

def test_attendance_rejects_attended_greater_than_total(client):
    login(client)
    with app_module.app.app_context():
        db = app_module.get_db()
        student = db.execute("SELECT id FROM students LIMIT 1").fetchone()
        course = db.execute("SELECT id FROM courses LIMIT 1").fetchone()

    resp = client.post(
        "/attendance",
        data={
            "student_id": student["id"],
            "course_id": course["id"],
            "total_classes": "10",
            "attended_classes": "15",
        },
        follow_redirects=True,
    )
    assert b"cannot be greater than total" in resp.data


# ---------------------------------------------------------------------------
# Marks / grading
# ---------------------------------------------------------------------------

def test_compute_grade_boundaries():
    assert app_module.compute_grade(95) == "A+"
    assert app_module.compute_grade(85) == "A"
    assert app_module.compute_grade(75) == "B"
    assert app_module.compute_grade(65) == "C"
    assert app_module.compute_grade(55) == "D"
    assert app_module.compute_grade(30) == "F"


def test_attendance_status_threshold():
    assert app_module.attendance_status(75) == "Good"
    assert app_module.attendance_status(74.9) == "Warning"


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

def test_api_students_requires_login(client):
    resp = client.get("/api/students", follow_redirects=False)
    assert resp.status_code == 302


def test_api_students_returns_json(client):
    login(client)
    resp = client.get("/api/students")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "roll_no" in data[0]


def test_api_stats_returns_json(client):
    login(client)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_students" in data
    assert "students_by_department" in data


# ---------------------------------------------------------------------------
# CSV export & 404
# ---------------------------------------------------------------------------

def test_csv_export(client):
    login(client)
    resp = client.get("/students/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["Content-Type"]
    assert b"Roll No" in resp.data


def test_404_page(client):
    resp = client.get("/this-route-does-not-exist")
    assert resp.status_code == 404
    assert b"404" in resp.data
