from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.forms.fields import Field

        Field.default_error_messages.update(
            {
                "required": "Kampu ne'e tenke hakerek.",
                "invalid": "Dadus la loos.",
            }
        )
