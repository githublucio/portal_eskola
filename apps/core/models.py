from urllib.parse import quote_plus

from django.db import models


class School(models.Model):
    """Singleton-style school profile used across the public portal."""

    name = models.CharField("Naran", max_length=255)
    short_name = models.CharField("Naran badak", max_length=50, blank=True)
    logo = models.ImageField("Logo", upload_to="school/", blank=True, null=True)
    description = models.TextField("Deskrisaun", blank=True)
    history = models.TextField("Istória", blank=True)
    vision = models.TextField("Visaun", blank=True)
    mission = models.TextField("Misaun", blank=True)
    address = models.CharField("Enderesu", max_length=255, blank=True)
    phone = models.CharField("Telefone", max_length=50, blank=True)
    email = models.EmailField("Korreiu", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    map_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    map_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "school profile"
        verbose_name_plural = "school profile"

    def __str__(self) -> str:
        return self.name

    @property
    def social_links(self) -> list[tuple[str, str, str]]:
        links = []
        if self.facebook_url:
            links.append(("Facebook", self.facebook_url, "bi-facebook"))
        if self.instagram_url:
            links.append(("Instagram", self.instagram_url, "bi-instagram"))
        if self.youtube_url:
            links.append(("YouTube", self.youtube_url, "bi-youtube"))
        return links

    @property
    def map_embed_src(self) -> str:
        if self.map_latitude is not None and self.map_longitude is not None:
            query = f"{self.map_latitude},{self.map_longitude}"
        else:
            query = quote_plus(self.address or "Atauro, Timor-Leste")
        return f"https://maps.google.com/maps?q={query}&z=14&hl=pt&output=embed"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> "School":
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Eskola Sekundária Téknika Vokasionál Públika Atauro",
                "short_name": "ESTVP Atauro",
                "description": (
                    "Portal ofisiál Eskola Sekundária Téknika Vokasionál "
                    "Públika Atauro."
                ),
                "address": "Atauro, Timor-Leste",
            },
        )
        return obj
