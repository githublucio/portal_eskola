from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone

from .roles import ALL_ROLES, SUPER_ADMIN


class User(AbstractUser):
    phone = models.CharField(max_length=40, blank=True)
    display_name = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.get_username()

    @property
    def public_name(self) -> str:
        if self.display_name:
            return self.display_name
        full = self.get_full_name().strip()
        return full or self.get_username()

    def role_names(self) -> list[str]:
        if self.is_superuser:
            return [SUPER_ADMIN]
        names = list(self.groups.values_list("name", flat=True))
        return [name for name in names if name in ALL_ROLES]

    def primary_role(self) -> str:
        roles = self.role_names()
        return roles[0] if roles else ""

    def has_role(self, role_name: str) -> bool:
        if role_name == SUPER_ADMIN and self.is_superuser:
            return True
        return self.groups.filter(name=role_name).exists()

    def can_access_dashboard(self) -> bool:
        return self.is_active and (
            self.is_staff or self.is_superuser or self.groups.exists()
        )


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Tama"
        LOGOUT = "logout", "Sai"
        CREATE = "create", "Kria"
        UPDATE = "update", "Atualiza"
        DELETE = "delete", "Hamos"
        VIEW = "view", "Haree"
        OTHER = "other", "Seluk"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"

    def __str__(self) -> str:
        who = self.user.get_username() if self.user_id else "system"
        return f"{self.created_at:%Y-%m-%d %H:%M} {who} {self.action}"


def ensure_role_groups() -> list[Group]:
    groups = []
    for name in ALL_ROLES:
        group, _ = Group.objects.get_or_create(name=name)
        groups.append(group)
    return groups
