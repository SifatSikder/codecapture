import os
import shutil
from django.http import JsonResponse
from classes.preprocessing import VideoProcessor

class VideoChecker:
    def __init__(self):
        pass
    def video_upload_with_validity(self,request,image_path,video_path):
        if not os.path.exists(image_path): os.makedirs(image_path)
        if os.path.exists(image_path): 
            shutil.rmtree(image_path)
            os.makedirs(image_path)
        if not os.path.exists(video_path): os.makedirs(video_path)
        if os.path.exists(video_path): 
            shutil.rmtree(video_path)
            os.makedirs(video_path)
        if not request.FILES.getlist('videos'): return JsonResponse({"error": "No files uploaded"}, status=400)

        video_urls = []
        for file in request.FILES.getlist('videos'):
            file_path = os.path.join(video_path, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks(): destination.write(chunk)
            video_urls.append(file_path)

        print("Note Generation Started")
        video_processor = VideoProcessor()
        video_processor.extract_images(video_path, image_path)
        video_processor.extract_unique_images(image_path)
