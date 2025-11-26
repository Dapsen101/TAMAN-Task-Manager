# Task Manager

A production-ready Django + HTML/CSS Task Manager that delivers end-to-end task tracking, analytics, and modern UI/UX. Users can register, manage their profiles, create/assign tasks, and visualize productivity with interactive charts.

## Features
- **Full Auth Flow**: register, login, logout, password reset with secure email links.
- **Task Management**: CRUD, status updates, categories, due dates, assignments, pagination, filtering + search.
- **Analytics Dashboard**: Chart.js visualizations for weekly productivity, completion trends, category distribution, and monthly summaries.
- **Responsive UI/UX**: Modern Poppins typography, card-based layout, hover states, and mobile-friendly pages.
- **Profile & Settings**: Editable user profile with avatar upload, settings shell for future preferences.
- **Production Hardened**: Env-based settings, secure middleware toggles, static/media pipelines, logging.

## Tech Stack
- Django 5.1
- SQLite (switchable to Postgres via env vars)
- Chart.js
- Bootstrap 5 + custom CSS

## Getting Started

### 1. Clone & Install
```bash
git clone <repo>
cd TAMAN-TASK-MANAGER-MAIN/taman_manager
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file (see `.env.example`) in `taman_manager/`:
```
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Add database/email credentials for production (e.g., PostgreSQL + SMTP).

### 3. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser  # optional
```

### 4. Run Locally
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/`.

## Deployment Notes
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`.
- Provide production database credentials in `.env`.
- Configure email backend for password reset (SMTP).
- Run `python manage.py collectstatic` and serve via WhiteNoise, S3, etc.
- Use HTTPS (settings already enforce HSTS/secure cookies when `DEBUG=False`).

## Analytics & Dashboard
- Metrics: totals, completion rate, productivity score, tasks per week/month.
- Charts: weekly productivity, category distribution, 30-day completion trend, monthly summary (completed vs pending).
- Data served via optimized ORM queries with caching-friendly context.

## Frontend Highlights
- Responsive cards, pagination, and filter bars.
- Consistent color palette, hover states, and button micro-interactions.
- Accessible contrast and form validation feedback.

## Testing Checklist
- [ ] `python manage.py test` (add tests as needed)
- [x] `python manage.py makemigrations && migrate`
- [x] Manual smoke test: auth, task CRUD, dashboard charts, filters/pagination.

## Folder Structure
```
taman_manager/
├── core/                # Django app
├── templates/           # HTML templates
├── static/              # CSS/JS/images
├── media/               # User uploads
├── manage.py
└── requirements.txt
```

## Improvements Summary
- Rebuilt analytics dashboard with Chart.js and rich metrics.
- Added task categories, due dates, completion timestamps for reporting.
- Implemented search/filter/sort + pagination + delete confirmation flows.
- Modernized all templates (dashboard, list, create/edit/delete, profiles).
- Hardened backend with login protection, env-based settings, security middleware.
- Added python-dotenv, static pipeline prep, logging, and deployment documentation.