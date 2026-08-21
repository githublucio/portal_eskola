from rest_framework.permissions import SAFE_METHODS, BasePermission, DjangoModelPermissions


class ReadOnlyOrDjangoModelPermissions(DjangoModelPermissions):
    """
    Anonymous/authenticated users may read.
    Write operations require Django model permissions.
    """

    authenticated_users_only = False

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )
