import os
import zipfile
import shutil
from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from api.preprocessing import VideoProcessor
from api.source_code_extraction import CodeExtractor
from api.summary_generation import TranscriptionAndSummaryGenerator
from api.workflow_extraction import WorkflowGenerator

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

def generate_notes_core():
    zip_file_path = os.path.join(settings.BASE_DIR, 'generated_note.zip')
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(settings.IMAGES_DIR):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), settings.IMAGES_DIR))
    return zip_file_path

@csrf_exempt
def generate_notes(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = generate_notes_core()
        return response_creator(zip_file_path)

def transcribe_video_core():
    transcription_summary_generator =TranscriptionAndSummaryGenerator()
    transcription_summary_generator.transcribe(settings.VIDEOS_DIR)
    transcriptions_dir = os.path.join(settings.BASE_DIR, "transcriptions")
    zip_file_path = os.path.join(settings.BASE_DIR, 'generated_transcription.zip')
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(transcriptions_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(transcriptions_dir)))
    return zip_file_path

@csrf_exempt
def transcribe_video(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = transcribe_video_core()
        print("Sending Transcriptions....")
        return response_creator(zip_file_path)
    
def summarize_video_core():
    transcription_summary_generator =TranscriptionAndSummaryGenerator()
    transcription_summary_generator.summarize(settings.VIDEOS_DIR)
    summaries_dir = os.path.join(settings.BASE_DIR, "summaries")
    zip_file_path = os.path.join(settings.BASE_DIR, 'generated_summary.zip')
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(summaries_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(summaries_dir)))
    return zip_file_path
    
@csrf_exempt
def summarize_video(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = summarize_video_core()
        print("Sending summaries....")
        return response_creator(zip_file_path)

def convert_to_long_path(path):
    """Convert path to extended-length format for Windows if needed."""
    if not path.startswith('\\\\?\\'):
        return f'\\\\?\\{os.path.abspath(path)}'
    return path

def extract_source_code_core():
    workflow_generator = WorkflowGenerator()
    workflow_generator.extract_text_from_whole_image("images")
    code_extractor = CodeExtractor()
    code_extractor.hierarchy_and_code_json_generation("ocr")
    code_extractor.create_hierarchies("hierarchy_json")
    code_extractor.create_codes("code_json")
    code_extractor.hierarchies_with_codes("individual_results")
    code_extractor.create_merged_hierarchies_json("hierarchy_json")
    code_extractor.create_merged_hierarchies("merged_results")
    code_extractor.create_merged_codes("code_json")
    code_extractor.create_merged_hierarchies_with_codes("merged_results")
    
    base_dir = settings.BASE_DIR
    results_path = os.path.join(base_dir, 'results')
    individual_results_path = os.path.join(settings.BASE_DIR, 'individual_results')
    merged_results_path = os.path.join(settings.BASE_DIR, 'merged_results')

    results_path = convert_to_long_path(results_path)
    individual_results_path = convert_to_long_path(individual_results_path)
    merged_results_path = convert_to_long_path(merged_results_path)
    if os.path.exists(f"{merged_results_path}/merged_hierarchy.json"): os.remove(f"{merged_results_path}/merged_hierarchy.json")
    
    if not os.path.exists(results_path): os.makedirs(results_path)
    dest_individual = os.path.join(results_path, 'individual_results')
    if not os.path.exists(dest_individual): shutil.copytree(individual_results_path, dest_individual)
    dest_merged = os.path.join(results_path, 'merged_results')
    if not os.path.exists(dest_merged): shutil.copytree(merged_results_path, dest_merged)
    
    zip_file_path = os.path.join(settings.BASE_DIR, 'extracted_source_code.zip')
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(results_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), results_path))
    return zip_file_path

@csrf_exempt
def extract_source_code(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = extract_source_code_core()
        print("Sending Source Code....")
        return response_creator(zip_file_path)

def extract_workflow_core():
    workflow_generator = WorkflowGenerator()
    workflow_generator.extract_text_from_whole_image("images")
    workflow_generator.workflow_generation("ocr")
    workflow_dir = os.path.join(settings.BASE_DIR, "workflow")
    zip_file_path = os.path.join(settings.BASE_DIR, 'generated_workflow.zip')
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(workflow_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(workflow_dir)))
    return zip_file_path

@csrf_exempt
def extract_workflow(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = extract_workflow_core()
        print("Sending workflows....")
        return response_creator(zip_file_path)
    
def generate_all_core():
    zip_file_paths = []
    source_code_zip_path = extract_source_code_core()    
    workflow_zip_path = extract_workflow_core()
    transcription_zip_path = transcribe_video_core()
    summary_zip_path = summarize_video_core()
    note_zip_path = generate_notes_core()

    zip_file_paths.append(source_code_zip_path)
    zip_file_paths.append(workflow_zip_path)
    zip_file_paths.append(transcription_zip_path)
    zip_file_paths.append(summary_zip_path)
    zip_file_paths.append(note_zip_path)
    
    all_results_dir = os.path.join(settings.BASE_DIR, "all_results")
    os.makedirs(all_results_dir,exist_ok=True)
    for zip_file_path in zip_file_paths:
        if os.path.exists(zip_file_path): shutil.copy(zip_file_path, all_results_dir)
    
    all_results_zip_file_path = os.path.join(settings.BASE_DIR, 'all_results.zip')
    with zipfile.ZipFile(all_results_zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root,_, files in os.walk(all_results_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(all_results_dir)))
    return all_results_zip_file_path

@csrf_exempt
def generate_all(request):
    if request.method == "POST":
        preprocessing(request)
        zip_file_path = generate_all_core()
        print("Sending all results....")
        return response_creator(zip_file_path)

def check_api(request):
    return JsonResponse({"message": "Your API is working!"})