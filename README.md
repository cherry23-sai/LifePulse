# LifePulse
Backend: Django + DRF + PostgreSQL (JWT, per-user isolated data, no admin, no seed data). Frontend: React (Vite).

## Backend
    cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
    cp .env.example .env   # fill DB + email settings
    python manage.py makemigrations accounts finance life && python manage.py migrate
    python manage.py runserver

## Email (welcome, first-login, 9 PM nightly reminder)
Set EMAIL_HOST_USER / EMAIL_HOST_PASSWORD in .env (your Oracle-account email; Gmail needs an App Password).
Nightly at 9 PM IST, add to crontab (`crontab -e`) on the server:
    0 21 * * * cd /path/backend && .venv/bin/python manage.py send_nightly_reminders

## Frontend
    cd frontend && npm install && npm run dev
