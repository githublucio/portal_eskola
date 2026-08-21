from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .audit import log_action
from .models import AuditLog


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    log_action(
        user=user,
        action=AuditLog.Action.LOGIN,
        message="User logged in",
        request=request,
        object_type="User",
        object_id=str(user.pk),
        object_repr=user.get_username(),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    log_action(
        user=user,
        action=AuditLog.Action.LOGOUT,
        message="User logged out",
        request=request,
        object_type="User",
        object_id=str(getattr(user, "pk", "") or ""),
        object_repr=user.get_username() if user else "",
    )
