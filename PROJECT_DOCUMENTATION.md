# Project Documentation

## 1. Project Title
**Student Management System using Python (Flask) and SQLite**

## 2. Abstract
The Student Management System (SMS) is a web-based application designed to
digitize and simplify the day-to-day record-keeping tasks of an academic
department. It replaces manual, paper-based or spreadsheet-based tracking
of student information, course catalogs, attendance, and examination
marks with a single, centralized, password-protected web application.
Built using the Flask micro-framework and a lightweight SQLite database,
the system provides full Create-Read-Update-Delete (CRUD) functionality
for students and courses, along with automated attendance-percentage and
grade calculations, database-backed search, CSV export, and a small REST
API for programmatic access to student data.

## 3. Problem Statement
Small and medium-sized academic departments frequently rely on manual
registers, Excel sheets, or a scattering of unconnected documents to track
student details, attendance, and marks. This approach is error-prone,
difficult to search, hard to back up, and does not scale as the number of
students grows. There is a need for a lightweight, easy-to-deploy system
that a single administrator can use to manage all of this information from
one dashboard, without requiring expensive infrastructure or specialized
IT support.

## 4. Existing System
Most small institutions currently use:
- Physical attendance registers and mark sheets
- Standalone Excel/Google Sheets files, often duplicated and inconsistent
- Ad-hoc scripts with no authentication or validation

These approaches lack data integrity (no enforced uniqueness or
relationships), have no built-in reporting, and provide no straightforward
way to search or export records.

## 5. Proposed System
The proposed system is a single-admin web application where:
- All student, course, attendance, and marks data lives in one relational
  SQLite database with proper primary/foreign keys and uniqueness
  constraints.
- Access is protected by session-based authentication with hashed
  passwords.
- Attendance percentages and exam grades are computed automatically and
  consistently, removing manual calculation errors.
- Data can be searched directly from the database and exported to CSV for
  offline reporting.
- A small REST API exposes student and statistics data as JSON for
  potential integration with other tools.

## 6. Objectives
1. Provide secure, authenticated access to student records.
2. Implement full CRUD operations for students and courses.
3. Automate attendance percentage and status calculation.
4. Automate marks totalling and grade assignment.
5. Provide database-driven search across key student fields.
6. Allow bulk export of student data as CSV.
7. Expose a minimal REST API for students and dashboard statistics.
8. Ensure the application runs locally with zero paid dependencies.

## 7. Scope
The system covers student records, course records, attendance tracking,
and marks/results management for a single institution/department managed
by one administrator account. It does not cover payroll, fee management,
timetabling, or multi-institution/multi-tenant scenarios; these are listed
under Future Enhancements.

## 8. Technologies Used
| Layer          | Technology                              |
|----------------|------------------------------------------|
| Backend        | Python 3, Flask 3                        |
| Database       | SQLite 3 (via Python's built-in `sqlite3`) |
| Frontend       | HTML5, CSS3 (custom, no external CDN), vanilla JavaScript |
| Templating     | Jinja2                                    |
| Auth/Security  | Flask sessions, Werkzeug password hashing |
| Testing        | pytest                                    |

## 9. Functional Requirements
- FR1: The system shall allow an admin to log in and log out securely.
- FR2: The system shall restrict all data pages to authenticated sessions.
- FR3: The system shall allow adding, viewing, editing, and deleting student records.
- FR4: The system shall allow adding, viewing, editing, and deleting course records.
- FR5: The system shall allow recording attendance per student/course and computing the percentage automatically.
- FR6: The system shall reject attendance entries where attended classes exceed total classes.
- FR7: The system shall allow recording internal/external marks per student/course and computing total + grade automatically.
- FR8: The system shall provide a database-backed search for students by roll number, name, email, or department.
- FR9: The system shall allow exporting all student records as a CSV file.
- FR10: The system shall expose `/api/students` and `/api/stats` as JSON endpoints.
- FR11: The system shall display a dashboard summarizing key counts and recent activity.

## 10. Non-Functional Requirements
- **Usability**: Clean, responsive UI usable on both desktop and mobile screens.
- **Security**: Passwords are hashed (never stored in plain text); all SQL queries are parameterized to prevent injection.
- **Portability**: Runs on Windows, macOS, and Linux with only Python and pip.
- **Maintainability**: Simple, well-commented, single-file Flask app understandable by a student developer.
- **Performance**: SQLite and Flask's development server comfortably handle the small-to-medium data volumes typical of a single department.
- **Reliability**: The database is created automatically and safely (via `CREATE TABLE IF NOT EXISTS`) so the app cannot crash on first run due to a missing schema.

## 11. System Architecture
The application follows a classic **server-rendered MVC-like architecture**:
- **Model**: SQLite tables accessed through parameterized SQL in `app.py` (no ORM, for simplicity and transparency).
- **View**: Jinja2 templates in `templates/`, styled by `static/css/style.css`.
- **Controller**: Flask route functions in `app.py` that handle requests, validate input, talk to the database, and render templates.

```
Browser  <-->  Flask routes (app.py)  <-->  SQLite (instance/students.db)
                     |
                Jinja2 templates + static CSS/JS
```

## 12. Modules
1. **Authentication Module** — login, logout, session management, password hashing.
2. **Dashboard Module** — aggregate statistics and quick actions.
3. **Student Management Module** — CRUD + search + pagination + CSV export.
4. **Course Management Module** — CRUD + search.
5. **Attendance Module** — record and validate attendance, compute percentage/status.
6. **Marks Module** — record marks, compute total and grade.
7. **REST API Module** — JSON endpoints for students and stats.

## 13. Database Design

### Tables

**users**
| Column         | Type    | Constraints                |
|-----------------|---------|------------------------------|
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT   |
| username        | TEXT    | UNIQUE, NOT NULL             |
| password_hash   | TEXT    | NOT NULL                     |
| created_at      | TEXT    | DEFAULT current timestamp    |

**students**
| Column      | Type    | Constraints              |
|-------------|---------|---------------------------|
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT |
| roll_no     | TEXT    | UNIQUE, NOT NULL           |
| name        | TEXT    | NOT NULL                   |
| email       | TEXT    | UNIQUE, NOT NULL           |
| phone       | TEXT    |                             |
| gender      | TEXT    |                             |
| dob         | TEXT    |                             |
| department  | TEXT    | NOT NULL                   |
| year        | INTEGER | NOT NULL                   |
| semester    | INTEGER | NOT NULL                   |
| address     | TEXT    |                             |
| created_at  | TEXT    | DEFAULT current timestamp  |

**courses**
| Column      | Type    | Constraints                |
|-------------|---------|------------------------------|
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT   |
| code        | TEXT    | UNIQUE, NOT NULL             |
| name        | TEXT    | NOT NULL                     |
| department  | TEXT    | NOT NULL                     |
| credits     | INTEGER | NOT NULL                     |
| created_at  | TEXT    | DEFAULT current timestamp    |

**attendance**
| Column            | Type    | Constraints                                        |
|-------------------|---------|------------------------------------------------------|
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT                            |
| student_id        | INTEGER | FOREIGN KEY -> students.id (ON DELETE CASCADE)       |
| course_id         | INTEGER | FOREIGN KEY -> courses.id (ON DELETE CASCADE)        |
| total_classes     | INTEGER | NOT NULL                                              |
| attended_classes  | INTEGER | NOT NULL                                              |
| created_at        | TEXT    | DEFAULT current timestamp                             |
|                   |         | UNIQUE(student_id, course_id)                        |

**marks**
| Column      | Type    | Constraints                                        |
|-------------|---------|------------------------------------------------------|
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT                            |
| student_id  | INTEGER | FOREIGN KEY -> students.id (ON DELETE CASCADE)       |
| course_id   | INTEGER | FOREIGN KEY -> courses.id (ON DELETE CASCADE)        |
| internal    | INTEGER | NOT NULL (0–40)                                       |
| external    | INTEGER | NOT NULL (0–60)                                       |
| created_at  | TEXT    | DEFAULT current timestamp                             |
|             |         | UNIQUE(student_id, course_id)                        |

## 14. ER Diagram Description
- One **student** can have many **attendance** records (one per course) → 1:N relationship between `students` and `attendance`.
- One **course** can have many **attendance** records (one per enrolled student) → 1:N relationship between `courses` and `attendance`.
- Together, `attendance` acts as an associative (junction) entity resolving the M:N relationship between students and courses for attendance tracking, with a uniqueness constraint preventing duplicate entries per (student, course) pair.
- The same pattern applies to **marks**: it is a junction entity resolving the M:N relationship between students and courses for examination results.
- **users** is a standalone entity with no foreign-key relationship to the academic data — it exists purely to gate access to the system.

## 15. Use Case Description
- **Admin logs in**: Actor submits credentials; system validates against the hashed password and starts a session, or shows an error.
- **Admin adds a student**: Actor fills the "Add Student" form; system validates required fields and uniqueness, then inserts the record.
- **Admin records attendance**: Actor selects a student and course and enters total/attended classes; system validates attended ≤ total, then inserts or updates the record and computes the percentage/status for display.
- **Admin enters marks**: Actor selects a student and course and enters internal/external marks; system validates the ranges, computes the total and grade, and stores the record.
- **Admin searches students**: Actor enters a search term and/or department filter; system queries the database directly and returns matching rows.
- **Admin exports students**: Actor clicks "Export CSV"; system streams a CSV file of all student records.
- **External tool calls the API**: A client authenticates via the login form/session and calls `/api/students` or `/api/stats` to retrieve JSON data.

## 16. Data Flow Description
1. The browser sends an HTTP request (GET/POST) to a Flask route.
2. If the route is protected, Flask checks the session for a valid `user_id`; unauthenticated requests are redirected to `/login`.
3. The route handler validates any submitted form data.
4. Valid requests execute parameterized SQL statements against `instance/students.db`.
5. Results are passed into a Jinja2 template (or serialized to JSON for API routes) and returned to the browser.
6. Derived values (attendance percentage/status, marks total/grade) are computed in Python at render time rather than stored redundantly, keeping the stored data as the single source of truth.

## 17. Implementation
The entire backend logic lives in a single, well-organized `app.py` file,
divided into clearly commented sections: configuration, database helpers,
authentication helpers, domain calculation helpers (grading/attendance),
and one route group per module (auth, dashboard, students, courses,
attendance, marks, CSV export, API, error handlers). Templates extend a
shared `base.html` layout providing a persistent sidebar and topbar. All
database access uses parameterized queries via Python's built-in
`sqlite3` module — no ORM was used, keeping the code transparent and easy
for a learning developer to follow, per the project's own requirements.

## 18. Testing
Testing was performed at two levels:

1. **Manual end-to-end testing** using a running instance of the Flask
   development server and scripted HTTP requests, covering: unauthenticated
   redirects, login (success and failure), dashboard rendering, the full
   student CRUD cycle (add/search/view/edit/delete), course creation,
   attendance validation (including the attended > total rejection case),
   marks validation and grade calculation, the `/api/students` and
   `/api/stats` endpoints, CSV export, the custom 404 page, and logout.
   All of these checks passed against the final code.

2. **Automated testing** with `pytest` (`tests/test_app.py`), using
   Flask's test client against a temporary, isolated SQLite database per
   test run (so tests never touch the real `instance/students.db`). The
   suite contains 21 tests covering database initialization, authentication,
   the dashboard, student CRUD and search, attendance/marks validation
   rules, the grading and attendance-status helper functions directly, the
   REST API, CSV export, and the 404 page. All 21 tests pass:

   ```
   ============================= test session starts ==============================
   collected 21 items
   tests/test_app.py ..................... [100%]
   ============================== 21 passed in ~3.5s ===============================
   ```

## 19. Screens / Pages
1. Login
2. Dashboard (stats cards, department breakdown, recent students, quick actions)
3. Students (search, department filter, paginated table, actions)
4. Add Student / Edit Student (shared form template)
5. Student Profile (detail view with that student's attendance and marks)
6. Courses (add form + searchable table + edit page)
7. Attendance (record form + records table with computed % and status)
8. Marks / Results (record form + records table with computed total and grade)
9. 404 Not Found

## 20. Advantages
- Zero paid software or external services required
- Simple, transparent codebase suitable for a learning developer
- Automatic, consistent attendance and grade calculations remove manual error
- Database-backed search scales better than client-side filtering
- CSV export enables easy offline reporting
- REST API allows future integration with other tools

## 21. Limitations
- Single admin role; no separate teacher/student logins
- No password-reset flow
- SQLite is well suited to a single department's data volume but is not
  designed for high-concurrency, multi-server deployments
- The Flask development server used for local running is not intended
  for production traffic

## 22. Future Enhancements
- Role-based access control (Admin, Teacher, Student portals)
- Email notifications for low attendance
- Bulk student import from CSV/Excel
- Charts/graphs for attendance and grade distribution trends
- Password-reset and multi-factor authentication
- Migration path to PostgreSQL/MySQL for larger institutions

## 23. Conclusion
This project demonstrates a complete, working full-stack web application
built with Python and Flask, covering authentication, relational database
design, CRUD operations, business-rule validation, computed reporting
metrics, a REST API, and automated testing. It fulfills the requirements
of an academic/internship submission while remaining simple enough to
extend, making it a solid foundation for further coursework or a
portfolio project.

## 24. References
See `REFERENCES.md` for the list of open-source GitHub repositories
consulted for general feature and structure inspiration during planning.
