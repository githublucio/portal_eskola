# PRD.md
# Product Requirements Document
## Sistema Informasaun Portal Escola Teknika Vokasional Públika iha Atauro

## 1. Product Vision
Portal web ne'e sei sai hanesan fonte informasaun oficial ba Escola Teknika Vokasional Públika iha Atauro no, iha fase posterior, sai fundasaun ba sistema gestão académica.

## 2. Target Users
### Public
- Prospective students
- Parents/guardians
- Community
- Partners
- General visitors

### Internal
- Super Admin
- School Admin
- Academic Staff
- Editor
- Teacher
- Student

## 3. MVP Scope
MVP includes:
- Public website
- School profile
- CMS pages
- News and announcements
- Events
- Courses
- Documents/downloads
- Gallery
- Contact form
- Authentication
- Admin dashboard
- Role/permission control
- Academic master data
- Students
- Teachers
- Enrollment
- Classes
- Basic audit/security

MVP excludes:
- Online payment
- Full grading system
- Attendance
- SMS integration
- Mobile application
- Complex ERP/accounting
- Payroll

## 4. Functional Requirements

### FR-001 Home
System must display:
- School identity
- Hero/banner
- Important announcements
- Latest news
- Upcoming events
- Featured courses
- Gallery highlights
- Contact information

### FR-002 School Profile
Admin can manage:
- Name
- Logo
- Description
- History
- Vision
- Mission
- Address
- Phone
- Email
- Social media
- Map coordinates

### FR-003 Pages
Authorized editors can:
- Create
- Read
- Update
- Publish/unpublish
- Archive
- Delete pages

Each page should have title, slug, content, image and SEO metadata.

### FR-004 News
Authorized users can:
- Create news
- Assign category
- Add featured image
- Save draft
- Publish
- Archive
- Edit/delete according to permission

Public users can:
- List news
- Open news detail
- Browse categories

### FR-005 Events
System must support:
- Event title
- Description
- Location
- Start/end date
- Organizer
- Image
- Publication status

Public users can browse upcoming/past events.

### FR-006 Courses
System must support:
- Department
- Course code
- Course name
- Description
- Duration
- Qualification
- Requirements
- Subjects

Public users can view published courses.

### FR-007 Students
Authorized academic staff can:
- Create student
- Edit student
- View student
- Search by student number/name
- Filter by status
- View enrollment history

Sensitive student information must not be publicly accessible.

### FR-008 Teachers
Authorized staff can:
- Create teacher
- Edit teacher
- View teacher
- Assign department
- Store specialization and qualification

### FR-009 Academic Year
Admin can create and activate academic years.
Only one academic year should normally be marked active unless business rules explicitly allow otherwise.

### FR-010 Enrollment
System must record:
- Student
- Course
- Academic year
- Enrollment number
- Enrollment date
- Status

Historical enrollments must remain available.

### FR-011 Classes
System must support:
- Course
- Academic year
- Class name
- Level
- Capacity
- Adviser/teacher

Student-class assignments must retain academic-year history.

### FR-012 Documents
Authorized users can upload documents.
Document must support:
- Title
- Category
- Description
- File
- Version
- Public/private status
- Uploaded by
- Published date

Public users can download only public/published documents.

### FR-013 Gallery
System must support:
- Albums
- Cover image
- Multiple photos
- Captions
- Ordering
- Publication status

### FR-014 Contact
Public users can send:
- Name
- Email
- Phone
- Subject
- Message

Staff can mark messages as read and record reply status.

### FR-015 Authentication
System must support:
- Login
- Logout
- Password hashing
- Password reset
- User activation/deactivation
- Profile

### FR-016 Authorization
Access must be controlled by Django Groups and Permissions.

Suggested permissions:
- view
- add
- change
- delete
- publish where custom permission is required

### FR-017 Dashboard
Dashboard should show:
- Total students
- Total teachers
- Total courses
- Total news
- Upcoming events
- Recent activity

Dashboard cards must respect user permissions.

### FR-018 Audit Log
Important administrative actions should record:
- User
- Action
- Model/object
- Timestamp
- Basic request metadata where appropriate

## 5. Non-Functional Requirements

### NFR-001 Security
- DEBUG=False in production.
- Secrets stored in environment variables.
- HTTPS in production.
- CSRF protection.
- Secure cookies in production.
- Permission checks server-side.
- Uploaded files validated.
- No sensitive student information in public endpoints.

### NFR-002 Performance
- Use pagination for large lists.
- Use `select_related`/`prefetch_related` where appropriate.
- Add database indexes for frequent searches.
- Optimize images before/while storing where practical.

### NFR-003 Usability
- Mobile-first.
- Bootstrap 5.
- Clear navigation.
- Portuguese/Tetun-friendly content structure.
- Accessible forms and readable typography.

### NFR-004 Maintainability
- Modular apps.
- Class-based or function-based views consistently per module.
- Reusable template partials.
- Meaningful model names.
- Automated tests.
- Documentation.

### NFR-005 Backup
Production must have:
- PostgreSQL backup strategy.
- Media backup strategy.
- Restore procedure.
- Regular backup verification.

## 6. Data Model Requirements

Core entities:
- User
- School
- Page
- NewsCategory
- News
- Event
- Department
- AcademicYear
- Course
- Subject
- Teacher
- Student
- Enrollment
- ClassRoom
- StudentClass
- DocumentCategory
- Document
- GalleryAlbum
- GalleryPhoto
- ContactMessage
- AuditLog

## 7. Main Relationships

```text
User 1 ─── * News
User 1 ─── * Document
User 1 ─── * Event

Department 1 ─── * Teacher
Department 1 ─── * Course
Course 1 ─── * Subject

Student 1 ─── * Enrollment
Course 1 ─── * Enrollment
AcademicYear 1 ─── * Enrollment

Course 1 ─── * ClassRoom
AcademicYear 1 ─── * ClassRoom
Teacher 1 ─── * ClassRoom

Student 1 ─── * StudentClass
ClassRoom 1 ─── * StudentClass
AcademicYear 1 ─── * StudentClass

NewsCategory 1 ─── * News
DocumentCategory 1 ─── * Document
GalleryAlbum 1 ─── * GalleryPhoto
Event 1 ─── 0..* GalleryAlbum
```

## 8. Public URL Requirements
- `/`
- `/about/`
- `/courses/`
- `/courses/<slug>/`
- `/news/`
- `/news/<slug>/`
- `/events/`
- `/events/<slug>/`
- `/documents/`
- `/gallery/`
- `/gallery/<slug>/`
- `/contact/`

## 9. Admin URL Requirements
- `/admin/`
- `/dashboard/`
- `/dashboard/news/`
- `/dashboard/events/`
- `/dashboard/courses/`
- `/dashboard/students/`
- `/dashboard/teachers/`
- `/dashboard/documents/`
- `/dashboard/gallery/`
- `/dashboard/users/`
- `/dashboard/settings/`

## 10. UI Requirements
### Public
Header:
- School logo
- School name
- Main navigation
- Language selector placeholder

Homepage:
- Hero
- About
- Courses
- News
- Events
- Gallery
- Contact

Footer:
- School identity
- Contact
- Quick links
- Social media
- Copyright

### Dashboard
- Sidebar
- Top navigation
- Breadcrumbs
- Statistics cards
- Tables
- Search
- Filters
- Pagination
- Create/Edit/Delete actions
- Confirmation before destructive actions

## 11. Roles and Access

| Feature | Super Admin | School Admin | Academic Staff | Editor | Teacher | Student |
|---|---|---|---|---|---|---|
| Users | Full | Limited | No | No | No | No |
| Settings | Full | Limited | No | No | No | No |
| News | Full | Full | View | Manage | View | View |
| Events | Full | Full | View | Manage | View | View |
| Courses | Full | Full | Manage | View | View | View |
| Students | Full | Manage | Manage | No | Limited | Own |
| Teachers | Full | Manage | Manage | View | Own | View |
| Enrollment | Full | Manage | Manage | No | View | Own |
| Documents | Full | Manage | Manage | Manage | View | View |
| Gallery | Full | Manage | View | Manage | View | View |

These permissions must be enforced server-side, not only hidden in the UI.

## 12. Acceptance Criteria
A feature is accepted when:
1. Authorized users can complete the intended workflow.
2. Unauthorized users receive HTTP 403 or are redirected appropriately.
3. Form validation works.
4. Database constraints prevent invalid relationships.
5. List pages support pagination where needed.
6. Public pages expose only published/public content.
7. Tests cover critical behavior.
8. No existing feature is broken.
9. Documentation is updated.

## 13. AI Development Rules
When generating each phase, AI must:
- Read `PLAN.md` and `PRD.md`.
- Inspect current code before editing.
- Respect existing architecture.
- Implement only the current phase.
- Never delete existing working functionality without explicit reason.
- Ask before making a breaking architectural change.
- Create migrations for model changes.
- Run tests after implementation.
- Fix errors before declaring completion.
- Update README/changelog when relevant.
- Provide a concise summary of changed files.
- Do not invent business requirements.

## 14. Definition of Done
The whole MVP is complete when:
- All MVP phases are implemented.
- Database migrations are clean.
- Critical tests pass.
- Role/permission checks work.
- Public portal works on desktop/mobile.
- Admin dashboard works.
- File uploads are validated.
- Security settings are production-ready.
- Backup and restore procedure is documented.
- Deployment documentation exists.

## 15. Future Roadmap
After MVP:
1. Attendance
2. Grades
3. Timetable
4. Student portal
5. Teacher portal
6. Certificates
7. Online application
8. Notifications
9. REST API
10. Mobile application
