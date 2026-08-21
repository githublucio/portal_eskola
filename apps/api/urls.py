from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    ApiRootView,
    CourseViewSet,
    DocumentViewSet,
    EventViewSet,
    MeView,
    NewsViewSet,
)

router = DefaultRouter()
router.register("news", NewsViewSet, basename="api-news")
router.register("events", EventViewSet, basename="api-events")
router.register("courses", CourseViewSet, basename="api-courses")
router.register("documents", DocumentViewSet, basename="api-documents")

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("auth/me/", MeView.as_view(), name="api-me"),
    path("", include(router.urls)),
]
