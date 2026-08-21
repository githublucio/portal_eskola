from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from apps.accounts.models import ensure_role_groups
from apps.accounts.rbac import apply_default_role_permissions
from apps.accounts.roles import SUPER_ADMIN


class Command(BaseCommand):
    help = "Create role groups and assign default permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite existing role permissions with the default RBAC map.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        groups = ensure_role_groups()

        for group in groups:
            if group.name == SUPER_ADMIN:
                apply_default_role_permissions(group)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{SUPER_ADMIN}: {group.permissions.count()} permissions"
                    )
                )
                continue

            if reset or group.permissions.count() == 0:
                apply_default_role_permissions(group)
                action = "reset" if reset else "seeded"
            else:
                action = "kept"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{group.name}: {group.permissions.count()} permissions ({action})"
                )
            )

        super_group = next(group for group in groups if group.name == SUPER_ADMIN)
        if super_group.permissions.count() == 0:
            super_group.permissions.set(Permission.objects.all())
        self.stdout.write(self.style.SUCCESS("Role groups ready."))
