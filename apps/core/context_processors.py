from .models import School


def school(request):
    user = getattr(request, "user", None)
    has_student_portal = bool(
        user
        and user.is_authenticated
        and hasattr(user, "student_profile")
    )
    has_teacher_portal = bool(
        user
        and user.is_authenticated
        and hasattr(user, "teacher_profile")
    )
    return {
        "school": School.get_solo(),
        "has_student_portal": has_student_portal,
        "has_teacher_portal": has_teacher_portal,
    }

