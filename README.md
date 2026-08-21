# Portal ESTVP Atauro

Sistema Informasaun Portal Escola Secundária Técnica Vocacional Pública Atauro.

Stack: **Python / Django 5 / PostgreSQL / Bootstrap 5**

## Current status

Phase 0–9 ready:

- Django project + modular apps
- Custom user model (`accounts.User`)
- PostgreSQL via `.env`
- Public pages: Home, About, Contact, News, Events, Documents, Gallery, Courses, CMS Pages
- School profile + contact form
- CMS content via admin (draft–published–archived)
- File validation for images/documents
- Private documents are not publicly downloadable
- Academic master data + enrollment/classes
- Login/logout/profile, role groups, dashboard, audit log
- Error pages, security hardening, CSV reports, backup scripts
- REST API `/api/v1/` (news, events, courses, documents + token auth)
- School management: attendance, grades, timetable, certificates, notifications
- Student/Teacher portals + online application (`/apply/`)
- Teacher portal can mark attendance and enter grades
- Staff dashboard can manage timetable, issue certificates, and send notifications
- Production deploy: Ubuntu + Nginx + Gunicorn (`DEPLOY.md`)

### Roles / RBAC

```powershell
python manage.py setup_roles
# optional: restore default permissions for every role
python manage.py setup_roles --reset
```

Groups: `SUPER_ADMIN`, `SCHOOL_ADMIN`, `ACADEMIC_STAFF`, `EDITOR`, `TEACHER`, `STUDENT`

Dashboard RBAC: http://127.0.0.1:8001/dashboard/roles/

- Super admin can edit the CRUD matrix for each role
- School admin can assign users to roles
- `setup_roles` without `--reset` keeps customizations already saved in the dashboard

Dashboard: http://127.0.0.1:8001/dashboard/  
Reports: http://127.0.0.1:8001/dashboard/reports/  
Student portal: http://127.0.0.1:8001/portal/student/ (user linked to Student)  
Teacher portal: http://127.0.0.1:8001/portal/teacher/ (user linked to Teacher)  
Apply: http://127.0.0.1:8001/apply/

### Demo data

```powershell
python manage.py seed_demo
# optional: reset demo passwords
python manage.py seed_demo --reset-demo-users
```

| User | Password | Portal |
|------|----------|--------|
| `aluno1` | `DemoAluno2026!` | `/portal/student/` |
| `prof1` | `DemoProf2026!` | `/portal/teacher/` |

### Backup / restore

```powershell
# Requires pg_dump / pg_restore on PATH
.\scripts\backup.ps1
.\scripts\restore.ps1 -DumpPath .\backups\db_YYYYMMDD_HHMMSS.dump -MediaZip .\backups\media_YYYYMMDD_HHMMSS.zip
```

### Production checklist

```powershell
python manage.py check_deploy
.\scripts\collectstatic.ps1
.\scripts\backup.ps1
```

In production `.env`: `DEBUG=False`, strong `SECRET_KEY`, real `ALLOWED_HOSTS`, and HTTPS flags (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `CSRF_TRUSTED_ORIGINS`). See `.env.example`.

Full Ubuntu + Nginx + Gunicorn steps: [`DEPLOY.md`](DEPLOY.md).

## Requirements

- Python 3.11+
- PostgreSQL (local)
- Git

## Setup

1. Create database in pgAdmin (or `psql`):

   ```sql
   CREATE DATABASE escola_atauro;
   ```

2. Copy environment file and edit password:

   ```powershell
   copy .env.example .env
   ```

3. Create / activate virtualenv and install deps:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Migrate and run:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver 127.0.0.1:8001
   ```

   Port **8001** is used so it does not conflict with other local Django apps on `8000`.

5. Open http://127.0.0.1:8001/

## API (`/api/v1/`)

Public read (published/public content only):

- `GET /api/v1/news/`
- `GET /api/v1/events/`
- `GET /api/v1/courses/`
- `GET /api/v1/documents/`

Auth:

```powershell
# Get token
curl -X POST http://127.0.0.1:8001/api/v1/auth/token/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"YOUR_PASSWORD\"}"

# Use token
curl http://127.0.0.1:8001/api/v1/auth/me/ -H "Authorization: Token YOUR_TOKEN"
```

Staff may pass `?all=1` to include drafts/private. Write endpoints require model permissions.

Browsable API: http://127.0.0.1:8001/api/v1/

## Tests

```powershell
python manage.py test
```

## Project layout

```text
portal_eskola/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
├── apps/
├── templates/
├── static/
└── media/
```

See `PLAN.md` and `PRD.md` for roadmap and requirements.
