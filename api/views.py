from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .classes.video_checker import VideoChecker
from .classes.output_generation import OutputGenerator
import os

@csrf_exempt
def generate_notes(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_notes_core(settings.BASE_DIR)
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def generate_notes_again(request):
    if request.method == "GET":
        print("Generating notes again...")
        output_generator = OutputGenerator()
        if os.path.exists("generated_note.zip"): os.remove("generated_note.zip")
        zip_file_path = output_generator.generate_notes_core(settings.BASE_DIR)
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def transcribe_video(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.transcribe_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending Transcriptions....")
        return output_generator.response_creator(zip_file_path)
    
@csrf_exempt
def summarize_video(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.summarize_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending summaries....")
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def extract_source_code(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_source_code_core(settings.BASE_DIR)
        print("Sending Source Code....")
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def extract_source_code_again(request):
    if request.method == "GET":
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_source_code_again(settings.BASE_DIR)
        print("Sending Source Code....")
        return output_generator.response_creator(zip_file_path)    

@csrf_exempt
def extract_workflow(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_workflow_core(settings.BASE_DIR)
        print("Sending workflows....")
        return output_generator.response_creator(zip_file_path)
@csrf_exempt
def extract_workflow_again(request):
    if request.method == "GET":
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_workflow_again(settings.BASE_DIR)
        print("Sending workflows....")
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def generate_all(request):
    if request.method == "POST":
        video_uploader = VideoChecker()
        video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_all_core(settings.BASE_DIR,settings.VIDEOS_DIR)
        print("Sending all results....")
        return output_generator.response_creator(zip_file_path)

def check_api(request):
    return JsonResponse({"message": "Your API is working!"})