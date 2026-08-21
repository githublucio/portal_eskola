from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserChangeForm

from .models import User


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Naran uza-na'in ka liafuan-sekrétu sala.",
        "inactive": "Konta ne'e la ativu.",
    }
    username = forms.CharField(
        label="Naran uza-na'in",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Naran uza-na'in", "autofocus": True}
        )
    )
    password = forms.CharField(
        label="Liafuan-sekrétu",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Liafuan-sekrétu"}
        )
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "display_name",
            "first_name",
            "last_name",
            "email",
            "phone",
        )
        labels = {
            "display_name": "Naran hatudu",
            "first_name": "Naran uluk",
            "last_name": "Naran ikus",
            "email": "Korreiu",
            "phone": "Telefone",
        }
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "old_password": "Liafuan-sekrétu agora",
            "new_password1": "Liafuan-sekrétu foun",
            "new_password2": "Konfirma liafuan-sekrétu foun",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            if name in labels:
                field.label = labels[name]
            field.help_text = ""


class DashboardUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_active",
            "groups",
        )
