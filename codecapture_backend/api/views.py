import os
import zipfile
import shutil
from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from api.preprocessing import extract_images, extract_unique_images
from api.summary_generation import transcribe , summarize


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
    extract_images(settings.VIDEOS_DIR, settings.IMAGES_DIR)
    extract_unique_images(settings.IMAGES_DIR)


@csrf_exempt
def generate_notes(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = os.path.join(settings.BASE_DIR, 'images.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(settings.IMAGES_DIR):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), settings.IMAGES_DIR))

        with open(zip_file_path, 'rb') as zip_file:
            response = HttpResponse(zip_file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
            return response

    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def transcribe_video(request):
    if request.method == "POST":
        preprocessing(request)
        transcribe(settings.VIDEOS_DIR)
        transcriptions_dir = os.path.join(settings.BASE_DIR, "transcriptions")
        transcriptions = []
        for filename in os.listdir(transcriptions_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(transcriptions_dir, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
                    transcriptions.append({"filename": filename, "content": content})
        print("Sending transcriptions....")
        return JsonResponse({"transcriptions": transcriptions}, status=200)
    
@csrf_exempt
def summarize_video(request):
    if request.method == "POST":
        preprocessing(request)
        summarize(settings.VIDEOS_DIR)
        summaries_dir = os.path.join(settings.BASE_DIR, "summaries")
        summaries = []
        for filename in os.listdir(summaries_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(summaries_dir, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
                    summaries.append({"filename": filename, "content": content})
        print("Sending summaries....")
        return JsonResponse({"summaries": summaries}, status=200)