from django.urls import path
from .views import generate_notes

urlpatterns = [
    path('generate_notes/', generate_notes),
]
