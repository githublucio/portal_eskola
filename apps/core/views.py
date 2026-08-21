from django.utils import timezone
from django.views.generic import TemplateView

from apps.courses.models import Course
from apps.courses.models import PublishStatus as CourseStatus
from apps.events.models import Event
from apps.events.models import PublishStatus as EventStatus
from apps.gallery.models import GalleryAlbum, GalleryPhoto
from apps.gallery.models import PublishStatus as GalleryStatus
from apps.news.models import News
from apps.news.models import PublishStatus as NewsStatus

from .models import School


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school"] = School.get_solo()
        published_news = News.objects.filter(
            status=NewsStatus.PUBLISHED
        ).select_related("category")
        context["announcements"] = published_news.filter(is_announcement=True)[:3]
        context["latest_news"] = published_news[:6]
        context["featured_courses"] = Course.objects.filter(
            status=CourseStatus.PUBLISHED
        ).select_related("department")[:3]
        context["upcoming_events"] = Event.objects.filter(
            status=EventStatus.PUBLISHED,
            start_at__gte=timezone.now(),
        ).order_by("start_at")[:3]
        gallery_albums = GalleryAlbum.objects.filter(
            status=GalleryStatus.PUBLISHED
        ).prefetch_related("photos")
        context["gallery_highlights"] = gallery_albums[:3]
        context["hero_slides"] = self._hero_slides(gallery_albums, published_news)
        return context

    def _hero_slides(self, gallery_albums, published_news):
        slides = []
        photos = (
            GalleryPhoto.objects.filter(album__status=GalleryStatus.PUBLISHED)
            .select_related("album")
            .order_by("album__published_at", "sort_order", "id")[:8]
        )
        for photo in photos:
            if not photo.image:
                continue
            slides.append(
                {
                    "url": photo.image.url,
                    "caption": photo.caption or photo.album.title,
                    "link": photo.album.get_absolute_url(),
                }
            )
        if slides:
            return slides

        for album in gallery_albums[:6]:
            if album.cover_image:
                slides.append(
                    {
                        "url": album.cover_image.url,
                        "caption": album.title,
                        "link": album.get_absolute_url(),
                    }
                )
        if slides:
            return slides

        for item in published_news:
            if item.featured_image:
                slides.append(
                    {
                        "url": item.featured_image.url,
                        "caption": item.title,
                        "link": item.get_absolute_url(),
                    }
                )
            if len(slides) >= 6:
                return slides

        for event in Event.objects.filter(status=EventStatus.PUBLISHED).order_by("-start_at")[:6]:
            if event.image:
                slides.append(
                    {
                        "url": event.image.url,
                        "caption": event.title,
                        "link": event.get_absolute_url(),
                    }
                )
        return slides[:8]


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school"] = School.get_solo()
        return context
