"""Dashboard navigation items with required permissions."""

NAV_ITEMS = [
    {
        "label": "Painél",
        "url_name": "accounts:dashboard",
        "icon": "home",
        "permissions": (),
    },
    {
        "label": "Notísia sira",
        "url_name": "accounts:dashboard_news",
        "permissions": ("news.view_news",),
    },
    {
        "label": "Eventu sira",
        "url_name": "accounts:dashboard_events",
        "permissions": ("events.view_event",),
    },
    {
        "label": "Kursu sira",
        "url_name": "accounts:dashboard_courses",
        "permissions": ("courses.view_course",),
    },
    {
        "label": "Estudante sira",
        "url_name": "accounts:dashboard_students",
        "permissions": ("students.view_student",),
    },
    {
        "label": "Profesór sira",
        "url_name": "accounts:dashboard_teachers",
        "permissions": ("teachers.view_teacher",),
    },
    {
        "label": "Dokumentu sira",
        "url_name": "accounts:dashboard_documents",
        "permissions": ("documents.view_document",),
    },
    {
        "label": "Imajen sira",
        "url_name": "accounts:dashboard_gallery",
        "permissions": ("gallery.view_galleryalbum",),
    },
    {
        "label": "Uza-na'in sira",
        "url_name": "accounts:dashboard_users",
        "permissions": ("accounts.view_user",),
    },
    {
        "label": "Papél no asesu",
        "url_name": "accounts:dashboard_roles",
        "permissions": ("accounts.view_user",),
    },
    {
        "label": "Kandidatura sira",
        "url_name": "accounts:dashboard_applications",
        "permissions": ("academics.view_onlineapplication",),
    },
    {
        "label": "Oráriu",
        "url_name": "academics:dashboard_timetable",
        "permissions": ("academics.view_timetableslot",),
    },
    {
        "label": "Sertifikadu sira",
        "url_name": "academics:dashboard_certificates",
        "permissions": ("academics.view_certificate",),
    },
    {
        "label": "Notifikasaun sira",
        "url_name": "academics:dashboard_notifications",
        "permissions": ("academics.add_notification",),
    },
    {
        "label": "Relatóriu sira",
        "url_name": "accounts:dashboard_reports",
        "permissions": (),
    },
    {
        "label": "Rejistu audit",
        "url_name": "accounts:dashboard_audit",
        "permissions": ("accounts.view_auditlog",),
    },
    {
        "label": "Konfigurasaun",
        "url_name": "accounts:dashboard_settings",
        "permissions": ("core.view_school", "core.change_school"),
    },
]


def visible_nav_items(user):
    items = []
    for item in NAV_ITEMS:
        perms = item["permissions"]
        if user.is_superuser or not perms or any(user.has_perm(p) for p in perms):
            items.append(item)
    return items
