# PLAN.md
# Sistema Informasaun Portal Escola Teknika Vokasional Públika iha Atauro

## 1. Objetivu
Kria portal web oficial ba Escola Teknika Vokasional Públika iha Atauro, ho CMS/admin no fundasaun akademiku ne'ebé bele dezenvolve ba Sistema Gestão Escola iha futuru.

## 2. Teknolojia
- Backend: Python + Django
- Database: PostgreSQL
- Frontend: Django Templates + Bootstrap 5 + JavaScript
- Web server production: Nginx + Gunicorn
- OS production: Ubuntu LTS
- Media: local storage iha development; bele muda ba object storage iha production
- API: Django REST Framework prepara ba fase posterior
- Authentication: Django Custom User + Groups + Permissions
- Version control: Git
- Environment variables: `.env`

## 3. Prinsípiu Arquitetura
- Modular Django apps.
- Custom User desde inísiu.
- PostgreSQL.
- Django ORM; la uza SQL direto se la nesesáriu.
- Business logic importante la tau hotu iha views.
- Reusable templates/components.
- Permissions ho Django Groups/Permissions.
- Slug ba conteúdo públiku.
- Audit log ba ações administrativas importantes.
- Mobile-first responsive UI.
- SEO básico.
- Security best practices.
- Database migration kontroladu.
- Tests ba model, permission, URL no fluxo CRUD importante.

## 4. Django Apps
- `accounts`: authentication, users, roles, permissions, audit.
- `core`: school/site settings.
- `pages`: static CMS pages.
- `news`: news, announcements, categories.
- `events`: events.
- `courses`: departments, courses, subjects, academic years.
- `students`: students, enrollment, classes/student-class.
- `teachers`: teachers.
- `documents`: document categories and downloads.
- `gallery`: albums and photos.
- `contact`: public contact messages.

## 5. Project Structure
```text
escola_atauro/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/
├── apps/
│   ├── accounts/
│   ├── core/
│   ├── pages/
│   ├── news/
│   ├── events/
│   ├── courses/
│   ├── students/
│   ├── teachers/
│   ├── documents/
│   ├── gallery/
│   └── contact/
├── templates/
├── static/
└── media/
```

## 6. Fases de Implementasaun

### Phase 0 — Project Foundation
Objetivu: setup project, environment, Git, PostgreSQL, settings, base template, static/media.
Output:
- Django project runs.
- PostgreSQL connected.
- `.env` configured.
- Base template works.
- Git repository initialized.
- Basic tests configured.

### Phase 1 — Public Portal Foundation
Objetivu: website public core.
Implement:
- Home
- Header/navbar
- Footer
- About
- Contact
- School information
- Responsive layout
Output:
- Public portal navigable.
- Reusable components.
- Basic SEO metadata.

### Phase 2 — CMS: Pages, News, Announcements
Implement:
- Page CRUD
- News category
- News CRUD
- Draft/published/archived
- Featured image
- Public listing/detail
- Search/filter basic
- Admin permissions
Output:
- Staff can manage website content without code.

### Phase 3 — Events, Documents, Gallery
Implement:
- Event CRUD
- Event detail/list
- Document categories
- Public/private documents
- File upload
- Gallery albums
- Gallery photos
- Media validation
Output:
- School can publish activities, documents and photos.

### Phase 4 — Academic Master Data
Implement:
- Department
- Academic Year
- Course
- Subject
- Teacher
- Student
- Relationships and validations
Output:
- Academic master data ready.

### Phase 5 — Enrollment and Classes
Implement:
- Enrollment
- ClassRoom
- StudentClass
- Academic history
- Student status
- Search/filter/pagination
Output:
- Student enrollment and class assignment work correctly.

### Phase 6 — Authentication, Roles and Dashboard
Implement:
- Login/logout
- Profile
- Groups
- Permissions
- Dashboard
- Role-based navigation
- Audit logs
Roles:
- SUPER_ADMIN
- SCHOOL_ADMIN
- ACADEMIC_STAFF
- EDITOR
- TEACHER
- STUDENT
Output:
- Secure administrative portal.

### Phase 7 — Quality, Security and Reporting
Implement:
- Automated tests
- Permission tests
- File validation
- CSRF/XSS/security hardening
- Audit log review
- Basic reports
- Error pages
- Backup/restore procedure
Output:
- Production-ready MVP.

### Phase 8 — API and Future Integration
Implement only after web MVP is stable:
- Django REST Framework
- `/api/v1/`
- Authentication
- News/events/courses/documents endpoints
- API permissions
Output:
- Backend ready for mobile app/future integrations.

### Phase 9 — Future School Management
Implemented:
- Attendance (teacher marks roster; student views own records)
- Grades (teacher enters scores; student views own grades)
- Timetable (staff dashboard CRUD; student/teacher views)
- Student portal
- Teacher portal
- Certificates (issue + print)
- Notifications (staff compose; portal inbox)
- Online application
- Advanced reports (CSV: attendance, grades, applications).

## 7. Rule for AI Generation
AI must work phase-by-phase. Before coding a phase:
1. Read `PRD.md`.
2. Read this `PLAN.md`.
3. Inspect existing project structure.
4. Do not overwrite working functionality unnecessarily.
5. Implement only the requested phase.
6. Run migrations.
7. Run tests.
8. Fix errors.
9. Update documentation.
10. Report files changed and tests executed.

## 8. Definition of Done
A phase is complete only when:
- Requested features work.
- No unresolved migration errors.
- No obvious permission bypass.
- Tests pass.
- Responsive UI works.
- Existing phases still work.
- README/docs are updated.
- Git commit is recommended with a clear message.

## 9. Important Constraints
- Do not build attendance/grades before academic master data and enrollment are stable.
- Do not expose private student data on public pages.
- Do not store passwords manually; use Django authentication.
- Do not put secrets in Git.
- Validate uploaded files.
- Use pagination for large lists.
- Use indexes/constraints where appropriate.
- Preserve academic history instead of overwriting historical enrollment.
