import os
import json
import cv2
import shutil
import re
from ultralytics import YOLO
from paddleocr import PaddleOCR
import google.generativeai as genai

def extract_sidebar(model_path,image_path,image_name,save_path):

    model = YOLO(model_path)
    image_path = os.path.join(image_path,image_name)
    results = model.predict(source=image_path, save=False)
    sidebars = []
    for box in results[0].boxes:
        class_id = int(box.cls)
        confidence = float(box.conf)
        if class_id == 0 and confidence > 0.75: sidebars.append({'bbox': box.xyxy[0],'confidence': confidence})
    if sidebars:
        best_sidebar = max(sidebars, key=lambda x: x['confidence'])
        x_min, y_min, x_max, y_max = map(int, best_sidebar['bbox'])
        image = cv2.imread(image_path)
        sidebar_image = image[y_min:y_max, x_min:x_max]
        cv2.imwrite(save_path, sidebar_image)
        print(f"Sidebar saved at {save_path}")
    else:
        print("No sidebar with confidence greater than 0.75 found.")

def extract_components():
    image_folder_path = "images"
    model = YOLO('model/weights/best.pt')
    classes = model.names
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    directories = [d for d in os.listdir(image_folder_path) if os.path.isdir(os.path.join(image_folder_path, d))]
    for directory in directories:
        dir_path = os.path.join(image_folder_path, directory)
        os.makedirs(os.path.join("components", directory), exist_ok=True)
        image_list = [file_name for file_name in os.listdir(dir_path) if os.path.splitext(file_name)[1].lower() in image_extensions]
        for image_file in image_list:
            current_image_path = os.path.join(dir_path, image_file)
            component_image_path = os.path.join("components", directory, image_file)
            results = model.predict(source=current_image_path, save=False)
            if len(results[0].boxes) > 0: 
                os.makedirs(component_image_path, exist_ok=True)
            for box in results[0].boxes:
                class_id = int(box.cls)
                confidence = float(box.conf)
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
                image = cv2.imread(current_image_path)
                image = image[y_min:y_max, x_min:x_max]
                current_component_image_path = os.path.join(component_image_path, f"{classes[class_id]}_{confidence:0.2f}.jpg")
                cv2.imwrite(current_component_image_path, image)

def convert_bbox_to_vertice(bbox):
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

def create_json_file(bboxes, texts,json_path):
  lines = []
  for i, (bbox, text) in enumerate(zip(bboxes, texts)):
    lines.append({"id": i,"text": text,"vertice": convert_bbox_to_vertice(bbox)})
  result= {"lines": lines}
  with open(json_path, 'w') as f:
    json.dump(result, f, indent=2)
  print(f'{json_path} is created...')

def extract_text_from_image():
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    for root, _, files in os.walk('components'):
        for file in files:
            image_path = os.path.join(root, file)
            json_path = os.path.join(root, f"{file}.json")
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
            create_json_file(bounding_boxes, texts,json_path)

def extract_sidebars_files_codes_codes_structures(response):
    sidebar_pattern = r'\\sidebar\s*\{(\s*\[.*?\]\s*)\}'
    active_files_pattern = r'\\activeFiles\s*\{(\s*\[.*?\]\s*)\}'
    codes_pattern = r'\\codes\s*\{(\s*\[.*?\]\s*)\}'
    code_structures_pattern = r'\\code_structures\s*\{(\s*\[.*?\]\s*)\}'
    extracted_sidebar = re.search(sidebar_pattern, response, re.DOTALL)
    extracted_sidebar = extracted_sidebar.group(1).strip() if extracted_sidebar else "Not found"
    
    extracted_active_files = re.search(active_files_pattern, response, re.DOTALL)
    extracted_active_files = extracted_active_files.group(1).strip() if extracted_active_files else "Not found"
    
    extracted_codes = re.search(codes_pattern, response, re.DOTALL)
    extracted_codes = extracted_codes.group(1).strip() if extracted_codes else "Not found"
    
    extracted_code_structures = re.search(code_structures_pattern, response, re.DOTALL)
    extracted_code_structures = extracted_code_structures.group(1).strip() if extracted_code_structures else "Not found"
    
    return extracted_sidebar, extracted_active_files, extracted_codes, extracted_code_structures

def read_json_text(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [line["text"] for line in data.get("lines", [])]

def merge_all_json(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'all_json' in dirpath: continue
        filenames = [f for f in filenames if f.endswith('.json')]
        if filenames:
            base_dir = os.path.abspath(os.path.join(dirpath, os.pardir))
            all_json_dir = os.path.join(base_dir, "all_json")
            os.makedirs(all_json_dir,exist_ok=True)            
            for file_name in filenames:
                old_file_path = os.path.join(dirpath, file_name)
                shutil.copy(old_file_path, all_json_dir)
                new_file_name = f"{os.path.basename(dirpath).split('.')[0]}_{file_name}"
                new_file_path = os.path.join(all_json_dir, new_file_name)
                copied_file_path = os.path.join(all_json_dir, file_name)
                os.rename(copied_file_path, new_file_path)

def compile_code(sidebars,activeFiles,codes):
    genai.configure(api_key="AIzaSyDJn8iLuEjbgsbVMog32wdEkWLSELH6-Q4")
    generation_config = {"temperature": 0.7,"top_p": 0.6,"top_k": 40,"max_output_tokens": 20*1024,"response_mime_type": "text/plain",}
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    prompt = f"""
    Generate the folder structure from the sidebar OCR texts: {sidebars}. An example of generated format of folder structure is shown below:
    \\sidebar{{'id':1, 'text': 'The New Boston', 'level':0, 'parent_id':null}}
    \\sidebar{{'id':2, 'text': 'Chapter 1', 'level':1, 'parent_id':1}}
    \\sidebar{{'id':3, 'text': 'Chapter 1.1', 'level':2, 'parent_id':'}}
    \\sidebar{{'id':4, 'text': 'Chapter 1.2', 'level':2, 'parent_id':2}}
    Put your final extracted structure within \\sidebar{{''}}.
    The final extracted structure must be start with \\sidebar{{ and end with }}.
    
    Next, generate the potential activeFile lists from the OCR texts: {activeFiles}. Consider all possible potential activeFiles and their probabilities.
    An example of generated format of activeFile list is shown below:
    \\activeFiles{['file1.extension', 'file2.extension', 'file3.extension', 'file4.extension']}
    Put your final extracted activeFiles list within \\activeFiles{{''}}.
    The final extracted activeFiles must be start with \\activeFiles{{ and end with }}.
    
    Then generate the code from the OCR texts: {codes}. Recheck again the codes to ensure that they are correct.
    If not then generate the codes again.
    An example of generated format of codes list is shown below:
    \\codes{['extracted_codes', 'extracted_codes',]}
    Put your final extracted codes within \\codes{{''}}.
    The final extracted codes must be start with \\codes{{ and end with }}.
    
    finally using the activeFiles and codes, generate the code structure dictionary like this: 
    \\code_structures{[{"activeFile": "file1.extension", "code": "extracted_codes"},{"activeFile": "file2.extension", "code": "extracted_codes"}]}.
    Put your final extracted code_structures within \\code_structures{{''}}.
    The final extracted code_structures must be start with \\code_structures{{ and end with }}.
    """
    print("Sending API request to generate code...Please wait...")
    response = chat_session.send_message(prompt)
    print("API response received.")
    return response.text

def cluster_classes (components_folder):
    for root, _ , files in os.walk(components_folder):
        if os.path.basename(root) == 'all_json':
            sidebars = []
            activeFiles = []
            codes = []
            for file in files:
                file_path = os.path.join(root, file)
                pieces = file.split("_")
                pieces[2] =pieces[2].split('.')[1]
                if pieces[1] == 'activeFile': activeFiles.append({'image_num':pieces[0], 'probability':pieces[2], 'texts':read_json_text(file_path),})
                if pieces[1] == 'code': codes.append({'image_num':pieces[0], 'probability':pieces[2], 'texts':read_json_text(file_path),})
                if pieces[1] == 'sidebar': sidebars.append({'image_num':pieces[0], 'probability':pieces[2], 'texts':read_json_text(file_path),})

            print(f'Video: {os.path.abspath(root)}')
            response = compile_code(sidebars,activeFiles,codes)
            extracted_sidebar, extracted_active_files, extracted_codes, extracted_code_structures = extract_sidebars_files_codes_codes_structures(response)

            print("Sidebar:", extracted_sidebar)
            print("ActiveFiles:", extracted_active_files)
            print("Codes:", extracted_codes)
            print("Code Structures:", extracted_code_structures)

# extract_components()
# extract_text_from_image()
# combine_filename_and_code()
# merge_all_json("components")
cluster_classes("components")