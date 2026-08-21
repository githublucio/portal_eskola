from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class FileExtensionValidator:
    def __init__(self, allowed_extensions):
        self.allowed_extensions = tuple(
            sorted({ext.lower().lstrip(".") for ext in allowed_extensions})
        )

    def __call__(self, file_obj):
        name = getattr(file_obj, "name", "") or ""
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in self.allowed_extensions:
            allowed = ", ".join(self.allowed_extensions)
            raise ValidationError(f"Tipu arkivu la simu. Permite: {allowed}.")

    def __eq__(self, other):
        return (
            isinstance(other, FileExtensionValidator)
            and self.allowed_extensions == other.allowed_extensions
        )


@deconstructible
class FileSizeValidator:
    def __init__(self, max_mb):
        self.max_mb = max_mb

    def __call__(self, file_obj):
        size = getattr(file_obj, "size", None)
        if size is not None and size > self.max_mb * 1024 * 1024:
            raise ValidationError(f"Arkivu boot liu. Máximu {self.max_mb} MB.")

    def __eq__(self, other):
        return isinstance(other, FileSizeValidator) and self.max_mb == other.max_mb


validate_image_file = [
    FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"]),
    FileSizeValidator(5),
]

validate_document_file = [
    FileExtensionValidator(["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip"]),
    FileSizeValidator(15),
]

validate_application_attachment = [
    FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
    FileSizeValidator(2),
]
