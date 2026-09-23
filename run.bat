@echo off
REM ============================================================
REM  Student Management System - Windows quick start script
REM ============================================================

IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Starting Student Management System...
echo Open http://127.0.0.1:5000 in your browser.
echo Demo login -  Username: admin   Password: admin123
python app.py

pause
