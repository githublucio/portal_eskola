from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views_errors import error_403, error_404, error_500

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("contact/", include("apps.contact.urls")),
    path("news/", include("apps.news.urls")),
    path("pages/", include("apps.pages.urls")),
    path("events/", include("apps.events.urls")),
    path("documents/", include("apps.documents.urls")),
    path("gallery/", include("apps.gallery.urls")),
    path("courses/", include("apps.courses.urls")),
    path("", include("apps.academics.urls")),
]

handler403 = error_403
handler404 = error_404
handler500 = error_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
