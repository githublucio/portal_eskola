from .models import AuditLog


def get_client_ip(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    *,
    user=None,
    action=AuditLog.Action.OTHER,
    obj=None,
    message="",
    request=None,
    object_type="",
    object_id="",
    object_repr="",
):
    if obj is not None:
        object_type = object_type or obj.__class__.__name__
        object_id = object_id or str(getattr(obj, "pk", "") or "")
        object_repr = object_repr or str(obj)[:255]

    return AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=object_id,
        object_repr=object_repr[:255],
        message=message,
        ip_address=get_client_ip(request),
        path=(request.path[:255] if request is not None else ""),
    )
