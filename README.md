# RAC HRMS — Rahman Anis & Co., Chartered Accountants

A production-ready web-based **HRMS** (Human Resource Management System) for managing Attendance, Leave, Payroll, Practice Management, Client Visits, and Conveyance for a Chartered Accountants firm.

---

## Tech Stack

| Layer      | Technology                            |
|------------|---------------------------------------|
| Backend    | Python 3.13, Django 5.2+              |
| Database   | SQLite (dev) / PostgreSQL (prod)      |
| Frontend   | Bootstrap 5, HTMX                     |
| PDF Export  | ReportLab                             |
| Excel Export| OpenPyXL                              |
| Server     | Gunicorn + Nginx                      |

---

## Modules

1. **Accounts** — Custom User model with Role-based access (Principal, Manager, Student)
2. **Students** — Student profiles linked to users
3. **Attendance** — Configurable policies, IN/OUT marking, working hour calculation
4. **Leave** — Leave types, hierarchical approval (Manager → Principal)
5. **Practice** — Client directory, Work Types, Assignments
6. **Conveyance** — Travel bill submission and approval
7. **Payroll** — Salary structures, automatic net pay calculation, PDF payslips
8. **Reports** — Filterable Attendance & Payroll reports with Excel export
9. **Dashboard** — Role-specific KPI dashboards

---

## Quick Start (Local Development)

```bash
# 1. Clone & enter directory
git clone <repo-url>
cd rac-erp-04082026

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Run server
python manage.py runserver
```

Visit `http://localhost:8000` and sign in.

---

## Production Deployment

1. Copy `.env.example` to `.env` and fill in production values.
2. Set `DJANGO_DEBUG=False`.
3. Run `python manage.py collectstatic`.
4. Start with Gunicorn: `gunicorn -c gunicorn.conf.py config.wsgi:application`.
5. Configure Nginx using `deploy/nginx.conf`.

---

## Running Tests

```bash
python manage.py test apps.core.tests --verbosity=2
```

---

## License

Internal use — Rahman Anis & Co., Chartered Accountants.
