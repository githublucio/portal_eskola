from django.db import models


class ContactMessage(models.Model):
    class ReplyStatus(models.TextChoices):
        PENDING = "pending", "Hein"
        REPLIED = "replied", "Responde"
        CLOSED = "closed", "Taka"

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    reply_status = models.CharField(
        max_length=20,
        choices=ReplyStatus.choices,
        default=ReplyStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contact message"
        verbose_name_plural = "contact messages"

    def __str__(self) -> str:
        return f"{self.subject} — {self.name}"
