from django.urls import path

from .views import NewsDetailView, NewsListView

app_name = "news"

urlpatterns = [
    path("", NewsListView.as_view(), name="list"),
    path("<slug:slug>/", NewsDetailView.as_view(), name="detail"),
]
