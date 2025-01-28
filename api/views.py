import os
import shutil
from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from api.preprocessing import VideoProcessor
from api.output_generation import OutputGenerator
def response_creator(zip_file_path):
    with open(zip_file_path, 'rb') as zip_file:
        response = HttpResponse(zip_file.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
        return response

def preprocessing(request):
    if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
    if os.path.exists(settings.IMAGES_DIR): 
        shutil.rmtree(settings.IMAGES_DIR)
        os.makedirs(settings.IMAGES_DIR)
    if not os.path.exists(settings.VIDEOS_DIR): os.makedirs(settings.VIDEOS_DIR)
    if os.path.exists(settings.VIDEOS_DIR): 
        shutil.rmtree(settings.VIDEOS_DIR)
        os.makedirs(settings.VIDEOS_DIR)
    if not request.FILES.getlist('videos'): return JsonResponse({"error": "No files uploaded"}, status=400)

    video_urls = []
    for file in request.FILES.getlist('videos'):
        file_path = os.path.join(settings.VIDEOS_DIR, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks(): destination.write(chunk)
        video_urls.append(file_path)

    print("Note Generation Started")
    video_processor = VideoProcessor()
    video_processor.extract_images(settings.VIDEOS_DIR, settings.IMAGES_DIR)
    video_processor.extract_unique_images(settings.IMAGES_DIR)

@csrf_exempt
def generate_notes(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_notes_core(settings.BASE_DIR)
        return response_creator(zip_file_path)

@csrf_exempt
def transcribe_video(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.transcribe_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending Transcriptions....")
        return response_creator(zip_file_path)
    
@csrf_exempt
def summarize_video(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.summarize_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending summaries....")
        return response_creator(zip_file_path)

@csrf_exempt
def extract_source_code(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_source_code_core(settings.BASE_DIR)
        print("Sending Source Code....")
        return response_creator(zip_file_path)

@csrf_exempt
def extract_workflow(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_workflow_core(settings.BASE_DIR)
        print("Sending workflows....")
        return response_creator(zip_file_path)

@csrf_exempt
def generate_all(request):
    if request.method == "POST":
        preprocessing(request)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_all_core(settings.BASE_DIR,settings.VIDEOS_DIR)
        print("Sending all results....")
        return response_creator(zip_file_path)

def check_api(request):
    return JsonResponse({"message": "Your API is working!"})