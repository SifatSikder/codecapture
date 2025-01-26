from django.urls import path
from .views import generate_notes , transcribe_video,summarize_video
urlpatterns = [
    path('generate_notes/', generate_notes),
    path('transcribe_video/', transcribe_video),
    path('summarize_video/', summarize_video),
]
