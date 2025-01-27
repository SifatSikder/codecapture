from django.urls import path
from .views import generate_notes , transcribe_video,summarize_video,extract_source_code,extract_workflow,generate_all
urlpatterns = [
    path('generate_notes/', generate_notes),
    path('transcribe_video/', transcribe_video),
    path('summarize_video/', summarize_video),    
    path('extract_source_code/', extract_source_code),
    path('extract_workflow/', extract_workflow),
    path('generate_all/', generate_all),
]
