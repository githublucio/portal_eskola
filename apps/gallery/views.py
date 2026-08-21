from django.views.generic import DetailView, ListView

from .models import GalleryAlbum, PublishStatus


class GalleryAlbumListView(ListView):
    model = GalleryAlbum
    template_name = "gallery/list.html"
    context_object_name = "albums"
    paginate_by = 9

    def get_queryset(self):
        return GalleryAlbum.objects.filter(
            status=PublishStatus.PUBLISHED
        ).prefetch_related("photos")


class GalleryAlbumDetailView(DetailView):
    model = GalleryAlbum
    template_name = "gallery/detail.html"
    context_object_name = "album"
    slug_field = "slug"

    def get_queryset(self):
        return GalleryAlbum.objects.filter(
            status=PublishStatus.PUBLISHED
        ).prefetch_related("photos")
