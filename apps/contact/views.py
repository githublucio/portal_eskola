from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from apps.core.models import School

from .forms import ContactMessageForm
from .models import ContactMessage


class ContactCreateView(CreateView):
    model = ContactMessage
    form_class = ContactMessageForm
    template_name = "contact/contact.html"
    success_url = reverse_lazy("contact:contact")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["school"] = School.get_solo()
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            "Obrigadu. Mensajen simu ona. Equipa sei responde iha tempu badak.",
        )
        return super().form_valid(form)
