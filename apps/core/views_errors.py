from django.shortcuts import render

from .models import School


def _school_context():
    return {"school": School.get_solo()}


def error_403(request, exception=None):
    return render(request, "errors/403.html", _school_context(), status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", _school_context(), status=404)


def error_500(request):
    return render(request, "errors/500.html", _school_context(), status=500)
