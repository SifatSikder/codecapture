from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .classes.video_checker import VideoChecker
from .classes.output_generation import OutputGenerator
import os
import shutil

@csrf_exempt
def generate_notes(request):
    if request.method == "POST":
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
            video_uploader = VideoChecker()
            video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_notes_core(settings.BASE_DIR,settings.IMAGES_DIR)
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
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
            video_uploader = VideoChecker()
            video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.transcribe_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending Transcriptions....")
        return output_generator.response_creator(zip_file_path)
    
@csrf_exempt
def summarize_video(request):
    if request.method == "POST":
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
            video_uploader = VideoChecker()
            video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.summarize_video_core(settings.VIDEOS_DIR,settings.BASE_DIR)
        print("Sending summaries....")
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def extract_source_code(request):
    if request.method == "POST":
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
            video_uploader = VideoChecker()
            video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.extract_source_code_core(settings.BASE_DIR,settings.IMAGES_DIR,settings.MODEL_DIR)
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
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
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
        if not os.path.exists(settings.IMAGES_DIR): os.makedirs(settings.IMAGES_DIR)
        if not os.listdir(settings.IMAGES_DIR):
            video_uploader = VideoChecker()
            video_uploader.video_upload_with_validity(request,settings.IMAGES_DIR,settings.VIDEOS_DIR)
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_all_core(settings.BASE_DIR,settings.VIDEOS_DIR)
        print("Sending all results....")
        return output_generator.response_creator(zip_file_path)
    
@csrf_exempt
def generate_all_again(request):
    if request.method == "GET":
        output_generator = OutputGenerator()
        zip_file_path = output_generator.generate_all_again(settings.BASE_DIR,settings.VIDEOS_DIR)
        print("Sending all results....")
        return output_generator.response_creator(zip_file_path)

@csrf_exempt
def delete_folders(request):
    if request.method == "POST":
        base_path = settings.BASE_DIR
        folders_to_delete = [
            "images", "videos", "code_json", "hierarchy_json", 
            "individual_results", "merged_results", "ocr", 
            "results","all_results", "summaries", "transcriptions","components"
        ]
        
        deleted_folders = []
        deleted_files = []

        for folder in folders_to_delete:
            folder_path = os.path.join(base_path, folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                deleted_folders.append(folder)

        for file in os.listdir(base_path):
            file_path = os.path.join(base_path, file)
            if file.endswith(".zip") and os.path.isfile(file_path):
                os.remove(file_path)
                deleted_files.append(file)

        return JsonResponse({
            "message": "Folders and zip files deleted",
            "deleted_folders": deleted_folders,
            "deleted_files": deleted_files
        })
    
    return JsonResponse({"error": "Invalid request"}, status=400)

def check_api(request):
    return JsonResponse({"message": "Your API is working!"})