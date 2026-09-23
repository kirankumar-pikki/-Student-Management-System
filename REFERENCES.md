# References & Inspiration

This project is an original implementation written for this submission. Before
building it, several open-source Flask + SQLite Student Management System
repositories were reviewed on GitHub for general feature ideas, common folder
layouts, and typical CRUD/authentication patterns. No code was copied from
any of these repositories — they were used purely as inspiration for scope
and structure, per the project requirements.

## Repositories reviewed

1. **sarthak-hello/Student-Management-System** (also mirrored as
   Harshal-Bsys27/student-management-system)
   https://github.com/sarthak-hello/Student-Management-System
   — Flask + SQLite + session auth + Bootstrap UI; informed the general
   "auth + dashboard + CRUD" shape of this project.

2. **BGourav05/Student-Management-System-using-Python**
   https://github.com/BGourav05/Student-Management-System-using-Python
   — Flask + SQLite app with role-based demo login and CSV import/export;
   the CSV export feature in this project was inspired by this idea
   (implemented independently here with Python's built-in `csv` module).

3. **adavidoaiei/Flask-Python**
   https://github.com/adavidoaiei/Flask-Python
   — A minimal Flask + SQLAlchemy CRUD example for student records; used as
   a reference for a simple, readable route-per-action structure.

4. **AzkhaM/WebAplication-Python** (fork/analysis of leevydanomalik/python-sqlite)
   https://github.com/AzkhaM/WebAplication-Python
   — Flask + Flask-SQLAlchemy student CRUD app with login; reviewed for
   template/page organization (login, list, add, edit pages).

5. **siarie/flask-crud-sqlite**
   https://github.com/siarie/flask-crud-sqlite
   — A small learning project demonstrating raw `sqlite3` CRUD operations in
   Flask without an ORM; informed the decision to use Python's built-in
   `sqlite3` module directly (with parameterized queries) instead of adding
   an ORM dependency, to keep the codebase approachable for a learner.

## What was built independently

Everything in this repository — the schema (`users`, `students`, `courses`,
`attendance`, `marks`), the attendance percentage / status logic, the
internal+external marks grading scale, the dashboard statistics, the REST
API (`/api/students`, `/api/stats`), the CSV export, the responsive sidebar
UI, the CSS design system, and the automated pytest test suite — was
designed and written from scratch for this academic submission. No files,
templates, or non-trivial code blocks were copied verbatim from any of the
repositories above.

## Licensing note

The repositories above are public GitHub projects intended for learning.
This project does not redistribute any of their source files. If you reuse
this project, treat it as an original work created for academic purposes.
