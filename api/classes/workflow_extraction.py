import os
import json
import cv2
import re
import google.generativeai as genai
from paddleocr import PaddleOCR

class WorkflowGenerator :
    def __init__(self):
        pass
    
    def convert_bbox_to_vertice(self, bbox):
        x_min = bbox[0][0]
        y_min = bbox[0][1]
        x_max = bbox[2][0]
        y_max = bbox[2][1]
        return {
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max
        }

    def create_json_file(self, bboxes, texts,json_path):
        lines = []
        for i, (bbox, text) in enumerate(zip(bboxes, texts)):
            lines.append({"id": i,"text": text,"vertice": self.convert_bbox_to_vertice(bbox)})
        result= {"lines": lines}
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'{json_path} is created...')

    def extract_text_from_whole_image(self, images_folder_path):
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        os.makedirs('ocr', exist_ok=True)
        for image_folder in os.listdir(images_folder_path):
            os.makedirs(os.path.join('ocr', image_folder), exist_ok=True)
            image_folder_path = os.path.join(images_folder_path, image_folder)
            for image in os.listdir(image_folder_path):
                image_path = os.path.join(image_folder_path, image)
                json_path = os.path.join('ocr', image_folder, f"{image}.json")
                image = cv2.imread(image_path)
                result = ocr.ocr(image)
                bounding_boxes =[]
                texts =[]
                for line in result:
                    if line is not None:
                        for word in line:
                            text = word[1][0]
                            bbox = word[0]
                            bounding_boxes.append(bbox)
                            texts.append(text)
                self.create_json_file(bounding_boxes, texts,json_path)

    def read_json_text(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return [line["text"] for line in data.get("lines", [])]

    def extract_workflow(self, frame_texts):    
        genai.configure(api_key="AIzaSyAkZBcCRUB4iKfn2BIIHNgX-v8s9y2Bk5I")
        generation_config = {"temperature": 1,"top_p": 0.95,"top_k": 40,"max_output_tokens": 20*1024,"response_mime_type": "text/plain",}
        model = genai.GenerativeModel(model_name="gemini-1.5-flash",generation_config=generation_config)
        chat_session = model.start_chat(history=[])
        prompt = f"""
        Here are extracted frames from the video tutorial, Frame Texts: {frame_texts}
        There might be some mistakes in the extracted texts.
        Please rectify the extracted texts.
        Now I want you to find out the step by step workflow of each frame in the code tutorial from the rectified texts.
        You will need to identify only 4 coding-steps in the workflow namely enter texts and delete texts, create file and delete file. 
        Each frame can have multiple actions or single action and even no action.
        If there is no action, you can skip that frame.
        If there is single or multiple actions, you need to identify the frame number, the code_filename, action/actions and the affected text/texts from the frame.
        An example of such a workflow is as follows:
        \\workflow{[{"frame":1,"workflow":[{"code_filename":"Splash.java","action":"create file","affected_text":"Created Splash.java"},{"code_filename":"Splash.java","action":"enter texts","affected_text":"Enter the text"},{"code_filename":"Splash.java","action":"delete texts","affected_text":"Delete the text"}] },{"frame":2,"workflow":[{"code_filename":"Splash.java","action":"delete file","affected_text":"deleted Splash.java"},{"code_filename":"Splash.java","action":"enter texts","affected_text":"Enter the text"},{"code_filename":"Splash.java","action":"delete texts","affected_text":"Delete the text"}] }]}
        Put your final extracted workflow within \\workflow{{''}}.
        The final extracted workflow must be start with \\workflow{{ and end with }}.
        """
        print("Sending API request to generate code...Please wait...")
        response = chat_session.send_message(prompt)
        print("API response received.")
        print(response.text)
        return response.text

    def workflow_generation (self, ocr_folders_path):
        os.makedirs('workflow', exist_ok=True)
        for ocr_folder in os.listdir(ocr_folders_path):
            ocr_folder_path = os.path.join(ocr_folders_path, ocr_folder)
            frame_texts = []
            for ocr_file in os.listdir(ocr_folder_path):
                ocr_file_path = os.path.join(ocr_folder_path, ocr_file)
                texts = self.read_json_text(ocr_file_path)
                frame_texts.append({"frame_num":ocr_file.split(".")[0],"texts":texts})
            response = self.extract_workflow(frame_texts)
            workflow_path = os.path.join('workflow', f"{ocr_folder}_workflow.txt")
            with open(workflow_path, "w", encoding="utf-8") as file:
                file.write(response)
            print(f"Workflow saved to {workflow_path}")
            # workflow_pattern = r"\\workflow\[(.*)\]"
            # extracted_workflow = re.search(workflow_pattern, response, re.DOTALL)
            # extracted_workflow = extracted_workflow.group(1).strip() if extracted_workflow else "Not found"
            # if extracted_workflow :
                # try:
                    # workflow_json = json.loads(f"[{extracted_workflow}]")
                    # workflow_array = [entry["workflow"] for entry in workflow_json]
                    # workflow_path = os.path.join('workflow', f"{ocr_folder}_workflow.json")
                    # with open(workflow_path, 'w', encoding='utf-8') as f: json.dump(workflow_array, f, indent=4, ensure_ascii=False)
                    # print(f"Workflow array saved to {workflow_path}")
                # except json.JSONDecodeError as e: workflow_array = f"Error decoding JSON: {e}"
            # else: print("Workflow array not found")
            


