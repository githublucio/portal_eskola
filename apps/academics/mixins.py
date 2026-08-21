from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


class LinkedProfileMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require login and a linked profile (student_profile / teacher_profile)."""

    profile_attr = ""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and hasattr(user, self.profile_attr)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        raise PermissionDenied

    def get_profile(self):
        return getattr(self.request.user, self.profile_attr)


class StudentPortalMixin(LinkedProfileMixin):
    profile_attr = "student_profile"

    def get_student(self):
        return self.get_profile()


class TeacherPortalMixin(LinkedProfileMixin):
    profile_attr = "teacher_profile"

    def get_teacher(self):
        return self.get_profile()
