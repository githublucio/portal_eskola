from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check common production readiness settings (non-destructive)."

    def handle(self, *args, **options):
        errors = []
        warnings = []

        if settings.DEBUG:
            errors.append("DEBUG is True — set DEBUG=False in production .env")

        secret = settings.SECRET_KEY or ""
        if not secret or secret.startswith("change-me") or len(secret) < 40:
            errors.append("SECRET_KEY is weak or still a placeholder")

        hosts = settings.ALLOWED_HOSTS or []
        if not hosts or hosts == ["*"]:
            errors.append("ALLOWED_HOSTS must be set to real hostnames")

        if not settings.SESSION_COOKIE_SECURE:
            warnings.append("SESSION_COOKIE_SECURE is False (enable with HTTPS)")
        if not settings.CSRF_COOKIE_SECURE:
            warnings.append("CSRF_COOKIE_SECURE is False (enable with HTTPS)")
        if not settings.SECURE_SSL_REDIRECT:
            warnings.append("SECURE_SSL_REDIRECT is False (enable behind HTTPS)")
        if not getattr(settings, "CSRF_TRUSTED_ORIGINS", None):
            warnings.append("CSRF_TRUSTED_ORIGINS is empty")

        if "rest_framework" not in settings.INSTALLED_APPS:
            warnings.append("DRF not installed in INSTALLED_APPS")

        self.stdout.write("Deploy check")
        self.stdout.write(f"  DEBUG={settings.DEBUG}")
        self.stdout.write(f"  ALLOWED_HOSTS={hosts}")
        self.stdout.write(
            f"  SECURE_SSL_REDIRECT={settings.SECURE_SSL_REDIRECT} "
            f"SESSION_COOKIE_SECURE={settings.SESSION_COOKIE_SECURE} "
            f"CSRF_COOKIE_SECURE={settings.CSRF_COOKIE_SECURE}"
        )

        for item in warnings:
            self.stdout.write(self.style.WARNING(f"WARNING: {item}"))
        for item in errors:
            self.stdout.write(self.style.ERROR(f"ERROR: {item}"))

        if errors:
            self.stdout.write(self.style.ERROR("Not ready for production."))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("Basic production checks passed."))
        if warnings:
            self.stdout.write(
                self.style.WARNING("Review warnings before going live.")
            )
