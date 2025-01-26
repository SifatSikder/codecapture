import os
import json
import cv2
import shutil
import re
from pathlib import Path
import google.generativeai as genai
from ultralytics import YOLO
from paddleocr import PaddleOCR
from collections import Counter

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

def extract_components(image_folder_path,model_path):
    model = YOLO(model_path)
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

def rectify_code_structures(extracted_code_structures):
    genai.configure(api_key="AIzaSyBM3HtmWkfS-Wu_fsk-JfnGHzoNLsLYjfQ")
    generation_config = {"temperature": 0.85,"top_p": 0.75,"top_k": 40,"max_output_tokens": 20*1024,"response_mime_type": "text/plain",}
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    prompt = f"""   
    Check the code structure: {extracted_code_structures}.
    Then carefully check whether the activeFile name corresponds to the code portion. If not, correct the activeFile name.
    Then carefully check whether there is any mistake in the code portion such as missing import,syntax error etc. If found any mistake rectify code portion.
    Put your final extracted rectified_code_structures within \\rectified_code_structures{{''}}.
    The final extracted rectified_code_structures must be start with \\rectified_code_structures{{ and end with }}.
    """
    print("Sending API request to rectify existing code structures if there is any mistake...Please wait...")
    response = chat_session.send_message(prompt)
    print("API response received.")
    print(f'rectified_code_structures: {response.text}')
    return response.text

def extract_sidebars_files_codes_codes_structures(response):
    sidebar_pattern = r'\\sidebar\s*\{(\s*\[.*?\]\s*)\}'
    extracted_sidebar = re.search(sidebar_pattern, response, re.DOTALL)
    extracted_sidebar = extracted_sidebar.group(1).strip() if extracted_sidebar else "Not found"
    
    active_files_pattern = r'\\activeFiles\s*\{(\s*\[.*?\]\s*)\}'
    extracted_active_files = re.search(active_files_pattern, response, re.DOTALL)
    extracted_active_files = extracted_active_files.group(1).strip() if extracted_active_files else "Not found"
    
    codes_pattern = r'\\codes\s*\{(\s*\[.*?\]\s*)\}'
    extracted_codes = re.search(codes_pattern, response, re.DOTALL)
    extracted_codes = extracted_codes.group(1).strip() if extracted_codes else "Not found"
    
    code_structures_pattern = r'\\code_structures\s*\{(\s*\[.*?\]\s*)\}'
    extracted_code_structures = re.search(code_structures_pattern, response, re.DOTALL)
    extracted_code_structures = extracted_code_structures.group(1).strip() if extracted_code_structures else "Not found"
    
    rectified_code_structures = rectify_code_structures(extracted_code_structures)
    rectified_code_structures_pattern = r'\\rectified_code_structures\s*\{(\s*\[.*?\]\s*)\}'
    extracted_rectified_code_structures = re.search(rectified_code_structures_pattern, rectified_code_structures, re.DOTALL)
    extracted_rectified_code_structures = extracted_rectified_code_structures.group(1).strip() if extracted_rectified_code_structures else "Not found"
    
    return extracted_sidebar, extracted_active_files, extracted_codes, extracted_code_structures,extracted_rectified_code_structures

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
    \\sidebar{{'id':1, 'text': 'The New Boston', 'level':0, 'parent_id':null, 'type':'folder'}},
    \\sidebar{{'id':2, 'text': 'Chapter 1', 'level':1, 'parent_id':1, 'type':'folder'}},
    \\sidebar{{'id':3, 'text': 'Chapter 1.1', 'level':2, 'parent_id':1, 'type':'folder'}},
    \\sidebar{{'id':4, 'text': 'a.txt', 'level':2, 'parent_id':2, 'type':'file'}},
    \\sidebar{{'id':5, 'text': 'hello.java', 'level':2, 'parent_id':2, 'type':'file'}},
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

def create_hierarchy_json(video_name,extracted_sidebar):
    folder_name = "hierarchy_json"
    os.makedirs(folder_name,exist_ok=True)
    file_path = os.path.join(folder_name, f"{video_name}.json")
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(extracted_sidebar, json_file, indent=4)

def create_code_json(video_name,extracted_rectified_code_structures):
    folder_name = "code_json"
    os.makedirs(folder_name,exist_ok=True)
    file_path = os.path.join(folder_name, f"{video_name}.json")
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(extracted_rectified_code_structures, json_file, indent=4)    

def hierarchy_and_code_json_generation (components_folder):
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

            video_name = os.path.abspath(root).split("\\")[-2]
            print(f'Video: {video_name}')
            response = compile_code(sidebars,activeFiles,codes)
            extracted_sidebar, extracted_active_files, extracted_codes, extracted_code_structures,extracted_rectified_code_structures = extract_sidebars_files_codes_codes_structures(response)

            print("Sidebar:", extracted_sidebar)
            print("ActiveFiles:", extracted_active_files)
            print("Codes:", extracted_codes)
            print("Code Structures:", extracted_code_structures)
            print("Rectified Code Structures:", extracted_rectified_code_structures)

            create_hierarchy_json(video_name,extracted_sidebar)
            create_code_json(video_name,extracted_rectified_code_structures)

def add_long_path_prefix(path):
    if os.name == 'nt': return f"\\\\?\\{os.path.abspath(path)}"
    return path

def create_structure(item, parent_path):
    full_path = os.path.join(parent_path, item['text'])
    if len(os.path.abspath(full_path)) >= 260: full_path = add_long_path_prefix(full_path)
    if item['type'] == 'folder': os.makedirs(full_path, exist_ok=True)
    elif item['type'] == 'file':
        with open(full_path, 'w') as file: pass
    return full_path

def create_hierarchy_from_json(json_file):
    os.makedirs("individual_results",exist_ok=True)
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    base_folder = f"individual_results/{base_name}"
    os.makedirs(base_folder,exist_ok=True)
    with open(json_file, 'r') as file:
        raw_data = file.read()
        raw_data = raw_data.replace("'", '"').replace("null", "None")
        # print("Raw data:", raw_data)
        regex_pattern = r'\{.*?\}'
        matches = re.findall(regex_pattern, raw_data)
        cleaned_list = [json.loads(match.replace("None", "null")) for match in matches]
        print('cleaned_list',cleaned_list)
        # print('type(cleaned_list[0])',type(cleaned_list[0]))
        
        id_to_path = {}
        for i,item in enumerate(cleaned_list):
            if item['parent_id'] is None:
                path = create_structure(item, base_folder)
            else:
                parent_path = id_to_path[item['parent_id']]
                path = create_structure(item, parent_path)
            id_to_path[item['id']] = path
    hierarchy_folder = os.path.join(base_folder, "hierarchy")   
    os.makedirs(hierarchy_folder, exist_ok=True)
    for item in os.listdir(base_folder):
        item_path = os.path.join(base_folder, item)
        if item_path != hierarchy_folder: shutil.move(item_path, hierarchy_folder)

def create_code_from_json(json_file):
    os.makedirs("individual_results",exist_ok=True)
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    base_folder = f"individual_results/{base_name}"
    os.makedirs(base_folder,exist_ok=True)
    with open(json_file, 'r') as file:
        raw_data = file.read()
        raw_data = raw_data.replace("'", '"')
        print("Raw data:", raw_data)
        print("Type of Raw data:", type(raw_data))
        try:
            code_data = json.loads(raw_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")
        
        print("Code data:", code_data)
        print("Type of code data:", type(code_data))
        print("Code data:", code_data[:10])
        
        # pattern = r'"activeFile":\s*"([^"]+)",\s*"code":\s*"([^"]+)"'
        pattern = r'"activeFile":\s*"([^"]+)",\s*"code":\s*"((?:\\.|[^\\"])*)"'
        matches = re.findall(pattern, code_data, re.DOTALL)
        extracted_data = {}
        for active_file, code in matches:
            code = bytes(code, "utf-8").decode("unicode_escape")
            extracted_data[active_file] = code
        print("extracted_data",extracted_data.keys())
        print("extracted_data",extracted_data.values())
        code_folder = os.path.join(base_folder, "code")
        os.makedirs(code_folder,exist_ok=True)
        for filename, code in extracted_data.items():
            file_path = os.path.join(code_folder, filename)
            with open(file_path, 'w') as file: file.write(code)
            print(f"Created file: {filename} with code:\n{code}\n")
            
        
        
        
        
        # transformed_data = [{"activeFile": entry["activeFile"], "codes": entry["code"]} for entry in code_data]
        # print(transformed_data)
        # return transformed_data
        # regex_pattern = r'\{.*?\}'
        # matches = re.findall(regex_pattern, raw_data)
        # cleaned_list = [json.loads(match.replace("None", "null")) for match in matches]
        # print('cleaned_list',cleaned_list)
        # print('type(cleaned_list[0])',type(cleaned_list[0]))

def create_hierarchies(hierarchy_folder):
    for root, _, files in os.walk(hierarchy_folder):
        for file in files:
            file_path = os.path.join(root, file)
            create_hierarchy_from_json(file_path)

def create_codes(code_folder):
    for root, _, files in os.walk(code_folder):
        for file in files:
            file_path = os.path.join(root, file)
            create_code_from_json(file_path)

def copy_everything_from_source_to_destination(source, destination):
    def add_long_path_prefix(path):
        if os.name == 'nt': return f"\\\\?\\{os.path.abspath(path)}"
        return path
    source = add_long_path_prefix(source)
    destination = add_long_path_prefix(destination)
    for item in os.listdir(source):
        source = os.path.join(source, item)
        destination = os.path.join(destination, item)
        if os.path.isdir(source): shutil.copytree(source, destination, dirs_exist_ok=True)
        else: shutil.copy2(source, destination)

def replace_matching_files(hierarchy_code_paths):
    for paths in hierarchy_code_paths:
        code_path = paths['code_path']
        hierarchy_path = paths['hierarchy_path']

        for root, dirs, files in os.walk(hierarchy_path):
            for file in files:
                hierarchy_file = os.path.abspath(os.path.join(root, file))
                if len(hierarchy_file) > 260: hierarchy_file = f"\\\\?\\{hierarchy_file}"
                code_file = os.path.abspath(os.path.join(code_path, file))
                if len(code_file) > 260: code_file = f"\\\\?\\{code_file}"
                if os.path.exists(code_file):
                    os.remove(hierarchy_file)
                    shutil.copy(code_file, hierarchy_file)
                    print(f"Replaced {hierarchy_file} with {code_file}")

def hierarchies_with_codes(final_results_folder):
    hierarchy_code_paths = []
    for video in os.listdir(final_results_folder):
        video_path = os.path.join(final_results_folder, video)
        hierarchy_with_code_path = os.path.join(video_path, "hierarchy_with_code")
        os.makedirs(hierarchy_with_code_path,exist_ok=True)
        if os.path.isdir(video_path):
            hierarchy_code_path = {}
            for folder_inside_video in os.listdir(video_path):
                if folder_inside_video == 'hierarchy':
                    hierarchy_path = os.path.join(video_path, folder_inside_video)
                    copy_everything_from_source_to_destination(hierarchy_path, hierarchy_with_code_path) 
                if folder_inside_video == 'code': hierarchy_code_path['code_path'] = os.path.join(video_path, folder_inside_video)
                if folder_inside_video == 'hierarchy_with_code': hierarchy_code_path['hierarchy_path'] = os.path.join(video_path, folder_inside_video)
            hierarchy_code_paths.append(hierarchy_code_path)

    replace_matching_files(hierarchy_code_paths)            

def create_merged_hierarchy_json(merged_hierarchy):
    file_path = os.path.join("merged_results", "merged_hierarchy.json")
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(merged_hierarchy, json_file, indent=4)

def create_merged_hierarchies_json(hierarchy_folder):
    hierarchies = []
    for filename in os.listdir(hierarchy_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(hierarchy_folder, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)
                hierarchies.append(json.dumps(json_data))
    
    genai.configure(api_key="AIzaSyCdgzxZnTZTemEPy8y3CZBGnCDHY4gnzyM")
    generation_config = {"temperature": 0.7,"top_p": 0.6,"top_k": 40,"max_output_tokens": 20*1024,"response_mime_type": "text/plain",}
    model = genai.GenerativeModel(model_name="gemini-1.5-flash",generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    prompt = f"""
    Take the list of hierarchies: {hierarchies}.
    next try to predict whether the hierarchies are mergeable or not.
    Give the mergeability prediction as a boolean value.
    put the answer within \\mergeability{{''}}.
    Next if it is mergeable then merge the hierarchies. An example of generated format of hierarchies is shown below:
    \\sidebar{{'id':1, 'text': 'The New Boston', 'level':0, 'parent_id':null, 'type':'folder'}},
    \\sidebar{{'id':2, 'text': 'Chapter 1', 'level':1, 'parent_id':1, 'type':'folder'}},
    \\sidebar{{'id':3, 'text': 'Chapter 1.1', 'level':2, 'parent_id':1, 'type':'folder'}},
    \\sidebar{{'id':4, 'text': 'a.txt', 'level':2, 'parent_id':2, 'type':'file'}},
    \\sidebar{{'id':5, 'text': 'hello.java', 'level':2, 'parent_id':2, 'type':'file'}},
    Put your final extracted structure within \\merged_hierarchy{{''}}.
    The final extracted structure must be start with \\merged_hierarchy{{ and end with }}.
    """
    response = chat_session.send_message(prompt)
    print("API response received.")
    print(f'Merged Hierarchies: {response.text}')
    
    mergeability_match = re.search(r"\\mergeability\{(true|false)\}", response.text)
    mergeability = mergeability_match.group(1) if mergeability_match else None

    merged_hierarchy_match = re.search(r"\\merged_hierarchy\{(.*)\}", response.text, re.DOTALL)
    merged_hierarchy = merged_hierarchy_match.group(1).strip() if merged_hierarchy_match else None
    
    if mergeability:
        os.makedirs("merged_results",exist_ok=True)
        create_merged_hierarchy_json(merged_hierarchy)

    print("Mergeability Value:", mergeability)
    print("Merged Hierarchies:\n", merged_hierarchy)
    
def create_merged_hierarchies(merged_hierarchy_json_folder):
    base_folder = f"{merged_hierarchy_json_folder}/merged_hierarchy"
    os.makedirs(base_folder,exist_ok=True)
    for filename in os.listdir(merged_hierarchy_json_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(merged_hierarchy_json_folder, filename)
            with open(file_path, 'r') as file:
                raw_data = file.read()
                raw_data = raw_data.replace("'", '"').replace("null", "None")
                regex_pattern = r'\{.*?\}'
                matches = re.findall(regex_pattern, raw_data)
                cleaned_list = [json.loads(match.replace("None", "null")) for match in matches]
                print('cleaned_list',cleaned_list)
                id_to_path = {}
                for i,item in enumerate(cleaned_list):
                    if item['parent_id'] is None:
                        path = create_structure(item, base_folder)
                    else:
                        parent_path = id_to_path[item['parent_id']]
                        path = create_structure(item, parent_path)
                    id_to_path[item['id']] = path
    
def create_merge_version(versions):
    genai.configure(api_key="AIzaSyBDg5VSfQ7e1dfcYRzEsJwIZu_Uch5vNm8")
    generation_config = {"temperature": 1,"top_p": 0.95,"top_k": 40,"max_output_tokens": 20*1024,"response_mime_type": "text/plain",}
    model = genai.GenerativeModel(model_name="gemini-1.5-pro",generation_config=generation_config)
    chat_session = model.start_chat(history=[])
    prompt = f"""
    Take the versions of a code: {versions}.
    Your task is to create a merged final version of this code.
    You must not write any comments in the final merged version.
    Put your final merged version within \\merged_version{{''}}.
    The final merged version must be start with \\merged_version{{ and end with }}.

    """
    response = chat_session.send_message(prompt)
    print("response = ",response.text)
    print("API response received.")
    return response.text

def create_merged_codes(code_folder):
    os.makedirs("merged_results",exist_ok=True)
    os.makedirs("merged_results/merged_codes",exist_ok=True)
    codes = []
    for filename in os.listdir(code_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(code_folder, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)
                codes.append(json.dumps(json_data))
    parsed_data = []
    for code in codes:
        json_string = code.strip('"')
        json_string = json_string.encode('utf-8').decode('unicode_escape')
        parsed_data.extend(json.loads(json_string))

    active_files = [item['activeFile'] for item in parsed_data if 'activeFile' in item]
    file_counts = Counter(active_files)
    unique_active_files = [file for file, count in file_counts.items() if count == 1]
    repeated_active_files = [file for file, count in file_counts.items() if count > 1]

    print("Unique Active Files:", unique_active_files)
    print("Repeated Active Files:", repeated_active_files)
    root = Path('./individual_results')
    files_in_code = []
    for code_folder in root.rglob("code"):
        if code_folder.is_dir():
            files_in_code.extend([file for file in code_folder.iterdir() if file.is_file()])
    repeated_active_file_dict = {}
    for repeated_file in repeated_active_files:
        repeated_active_file_dict[repeated_file] = []
    for file in files_in_code:
        if file.name in unique_active_files:  
            destination_path = f"merged_results/merged_codes/{file.name}" 
            shutil.copy(file, destination_path)
            print(f"Copied {file} to {destination_path}")
        if file.name in repeated_active_files:
            if file.exists() and file.is_file():
                with open(file, 'r', encoding='utf-8') as f:
                    repeated_active_file_dict[file.name].append(f.read())
    for filename, versions in repeated_active_file_dict.items():
        print("filename",filename)
        print("versions",versions)
        merged_version = create_merge_version(versions)
        destination_path = f"merged_results/merged_codes/{filename}"
        with open(destination_path, 'w', encoding='utf-8') as f:
            f.write(merged_version)
            
def create_merged_hierarchies_with_codes(merged_hierarchy_json_folder):
    hierarchy_with_code_path = os.path.join(merged_hierarchy_json_folder, "merged_hierarchy_with_code")
    os.makedirs(hierarchy_with_code_path,exist_ok=True)
    hierarchy_code_path = {}
    for folder_inside_video in os.listdir(merged_hierarchy_json_folder):
        if folder_inside_video == 'merged_hierarchy':
            hierarchy_path = os.path.join(merged_hierarchy_json_folder, folder_inside_video)
            copy_everything_from_source_to_destination(hierarchy_path, hierarchy_with_code_path) 
        if folder_inside_video == 'merged_codes': hierarchy_code_path['code_path'] = os.path.join(merged_hierarchy_json_folder, folder_inside_video)
        if folder_inside_video == 'merged_hierarchy_with_code': hierarchy_code_path['hierarchy_path'] = os.path.join(merged_hierarchy_json_folder, folder_inside_video)
    replace_matching_files([hierarchy_code_path])