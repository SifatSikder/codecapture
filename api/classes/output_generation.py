import os
import zipfile
import shutil
from .source_code_extraction import CodeExtractor
from .summary_generation import TranscriptionAndSummaryGenerator
from .workflow_extraction import WorkflowGenerator
from django.http import HttpResponse

class OutputGenerator:
    def __init__(self):
        pass
    def generate_notes_core(self,note_zip_path):
        zip_file_path = os.path.join(note_zip_path, 'generated_note.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(note_zip_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), note_zip_path))
        return zip_file_path
    def transcribe_video_core(self,video_path,base_path):
        transcription_summary_generator = TranscriptionAndSummaryGenerator()
        transcription_summary_generator.transcribe(video_path)
        transcriptions_dir = os.path.join(base_path, "transcriptions")
        zip_file_path = os.path.join(base_path, 'generated_transcription.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(transcriptions_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(transcriptions_dir)))
        return zip_file_path
    def summarize_video_core(self,video_path,base_path):
        transcription_summary_generator =TranscriptionAndSummaryGenerator()
        transcription_summary_generator.summarize(video_path)
        summaries_dir = os.path.join(base_path, "summaries")
        zip_file_path = os.path.join(base_path, 'generated_summary.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(summaries_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(summaries_dir)))
        return zip_file_path
    def convert_to_long_path(self,path):
        """Convert path to extended-length format for Windows if needed."""
        if not path.startswith('\\\\?\\'):
            return f'\\\\?\\{os.path.abspath(path)}'
        return path
    def extract_source_code_core(self,base_path):
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
        
        results_path = os.path.join(base_path, 'results')
        individual_results_path = os.path.join(base_path, 'individual_results')
        merged_results_path = os.path.join(base_path, 'merged_results')

        results_path = self.convert_to_long_path(results_path)
        individual_results_path = self.convert_to_long_path(individual_results_path)
        merged_results_path = self.convert_to_long_path(merged_results_path)
        if os.path.exists(f"{merged_results_path}/merged_hierarchy.json"): os.remove(f"{merged_results_path}/merged_hierarchy.json")
        
        if not os.path.exists(results_path): os.makedirs(results_path)
        dest_individual = os.path.join(results_path, 'individual_results')
        if not os.path.exists(dest_individual): shutil.copytree(individual_results_path, dest_individual)
        dest_merged = os.path.join(results_path, 'merged_results')
        if not os.path.exists(dest_merged): shutil.copytree(merged_results_path, dest_merged)
        
        zip_file_path = os.path.join(base_path, 'extracted_source_code.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(results_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), results_path))
        return zip_file_path
    
    def extract_source_code_again(self,base_path):
        if os.path.exists("hierarchy_json") : shutil.rmtree("hierarchy_json")
        if os.path.exists("code_json") : shutil.rmtree("code_json")
        if os.path.exists("individual_results") : shutil.rmtree("individual_results")
        if os.path.exists("merged_results") : shutil.rmtree("merged_results")
        if os.path.exists("extracted_source_code.zip") : os.remove("extracted_source_code.zip")
        
        code_extractor = CodeExtractor()
        code_extractor.hierarchy_and_code_json_generation("ocr")
        code_extractor.create_hierarchies("hierarchy_json")
        code_extractor.create_codes("code_json")
        code_extractor.hierarchies_with_codes("individual_results")
        code_extractor.create_merged_hierarchies_json("hierarchy_json")
        code_extractor.create_merged_hierarchies("merged_results")
        code_extractor.create_merged_codes("code_json")
        code_extractor.create_merged_hierarchies_with_codes("merged_results")
        
        results_path = os.path.join(base_path, 'results')
        individual_results_path = os.path.join(base_path, 'individual_results')
        merged_results_path = os.path.join(base_path, 'merged_results')

        results_path = self.convert_to_long_path(results_path)
        individual_results_path = self.convert_to_long_path(individual_results_path)
        merged_results_path = self.convert_to_long_path(merged_results_path)
        if os.path.exists(f"{merged_results_path}/merged_hierarchy.json"): os.remove(f"{merged_results_path}/merged_hierarchy.json")
        
        if not os.path.exists(results_path): os.makedirs(results_path)
        dest_individual = os.path.join(results_path, 'individual_results')
        if not os.path.exists(dest_individual): shutil.copytree(individual_results_path, dest_individual)
        dest_merged = os.path.join(results_path, 'merged_results')
        if not os.path.exists(dest_merged): shutil.copytree(merged_results_path, dest_merged)
        
        zip_file_path = os.path.join(base_path, 'extracted_source_code.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(results_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), results_path))
        return zip_file_path
    
    
    def extract_workflow_core(self,base_path):
        workflow_generator = WorkflowGenerator()
        workflow_generator.extract_text_from_whole_image("images")
        workflow_generator.workflow_generation("ocr")
        workflow_dir = os.path.join(base_path, "workflow")
        zip_file_path = os.path.join(base_path, 'generated_workflow.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(workflow_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(workflow_dir)))
        return zip_file_path
    
    def extract_workflow_again(self,base_path):
        if os.path.exists("workflow") : shutil.rmtree("workflow")
        if os.path.exists("generated_workflow.zip") : os.remove("generated_workflow.zip")
        workflow_generator = WorkflowGenerator()
        workflow_generator.workflow_generation("ocr")
        workflow_dir = os.path.join(base_path, "workflow")
        zip_file_path = os.path.join(base_path, 'generated_workflow.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(workflow_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(workflow_dir)))
        return zip_file_path
    
    def generate_all_core(self,video_path,base_path):
        zip_file_paths = []
        source_code_zip_path = self.extract_source_code_core(base_path)    
        workflow_zip_path = self.extract_workflow_core(base_path)
        transcription_zip_path = self.transcribe_video_core(video_path,base_path)
        summary_zip_path = self.summarize_video_core(video_path,base_path)
        note_zip_path = self.generate_notes_core(base_path)

        zip_file_paths.append(source_code_zip_path)
        zip_file_paths.append(workflow_zip_path)
        zip_file_paths.append(transcription_zip_path)
        zip_file_paths.append(summary_zip_path)
        zip_file_paths.append(note_zip_path)
        
        all_results_dir = os.path.join(base_path, "all_results")
        os.makedirs(all_results_dir,exist_ok=True)
        for zip_file_path in zip_file_paths:
            if os.path.exists(zip_file_path): shutil.copy(zip_file_path, all_results_dir)
        
        all_results_zip_file_path = os.path.join(base_path, 'all_results.zip')
        with zipfile.ZipFile(all_results_zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,_, files in os.walk(all_results_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(all_results_dir)))
        return all_results_zip_file_path
    def response_creator(self,zip_file_path):
        with open(zip_file_path, 'rb') as zip_file:
            response = HttpResponse(zip_file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_file_path)}'
            return response
