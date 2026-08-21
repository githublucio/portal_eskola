from django import forms

from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "Naran kompletu",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "email@ezemplu.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control bg-white",
                    "placeholder": "Numeru telefone (opsionál)",
                }
            ),
            "subject": forms.TextInput(
                attrs={"class": "form-control bg-white", "placeholder": "Asuntu"}
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control bg-white flex-grow-1",
                    "rows": 5,
                    "placeholder": "Hakerek mensajen iha ne'e...",
                }
            ),
        }
        labels = {
            "name": "Naran",
            "email": "Korreiu",
            "phone": "Telefone",
            "subject": "Asuntu",
            "message": "Mensajen",
        }
