from django.urls import path
from .views import generate_notes , transcribe_video,summarize_video,extract_source_code
urlpatterns = [
    path('generate_notes/', generate_notes),
    path('transcribe_video/', transcribe_video),
    path('summarize_video/', summarize_video),    
    path('extract_source_code/', extract_source_code),
]
