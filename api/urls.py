from django.urls import path
from .views import generate_notes, generate_notes_again , transcribe_video,summarize_video,extract_source_code,extract_workflow,generate_all,check_api, transcribe_video_again
urlpatterns = [
    path('generate_notes/', generate_notes),
    path('transcribe_video/', transcribe_video),
    path('summarize_video/', summarize_video),    
    path('extract_source_code/', extract_source_code),
    path('extract_workflow/', extract_workflow),
    path('generate_all/', generate_all),
    path('check_api/', check_api),
    path('generate_notes/generate_again', generate_notes_again),
    path('transcribe_video/generate_again', transcribe_video),
    path('summarize_video/generate_again', summarize_video),    
    path('extract_source_code/generate_again', check_api),
    path('extract_workflow/generate_again', check_api),
    path('generate_all/generate_again', check_api),
]
