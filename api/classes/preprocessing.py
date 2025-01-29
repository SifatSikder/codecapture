import os
import cv2
from skimage.metrics import structural_similarity as compare_ssim


class VideoProcessor:
    def __init__(self):
        pass

    def rename_images(self,directory_path):
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        image_list = [file_name for file_name in os.listdir(directory_path) if os.path.splitext(file_name)[1].lower() in image_extensions]
        image_list.sort()

        for index, image_file in enumerate(image_list, start=1):
            new_name = f"{index:05d}{os.path.splitext(image_file)[1]}"
            old_file_path = os.path.join(directory_path, image_file)
            new_file_path = os.path.join(directory_path, new_name)
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {image_file} -> {new_name}")

    def compare_frame(self,frameA, frameB):
        grayA = cv2.cvtColor(frameA, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(frameB, cv2.COLOR_BGR2GRAY)
        score, diff = compare_ssim(grayA, grayB, full=True)
        diff = (diff * 255).astype("uint8")
        thresh = cv2.threshold(diff, 180, 255, cv2.THRESH_BINARY_INV)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0]
        return diff, thresh, cnts, score

    def extract_images(self,video_folder_path,image_folder_path):
        video_extensions = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
        for video_file_name in os.listdir(video_folder_path):
            video_file_path = os.path.join(video_folder_path, video_file_name)
            if os.path.isfile(video_file_path) and os.path.splitext(video_file_name)[1].lower() in video_extensions:
                image_path = os.path.join(image_folder_path, video_file_name)
                if not os.path.exists(image_path):
                    os.makedirs(image_path, exist_ok=True)
                    cmd = f'ffmpeg -i "{video_file_path}" -q:v 1 -r 1 "{image_path}/%05d.jpg"'
                    os.system(cmd)

    def extract_unique_images(self,image_folder_path):
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        directories = [d for d in os.listdir(image_folder_path) if os.path.isdir(os.path.join(image_folder_path, d))]
        for directory in directories:
            for _ in range(3):
                dir_path = os.path.join(image_folder_path, directory)
                image_list = [file_name for file_name in os.listdir(dir_path) if os.path.splitext(file_name)[1].lower() in image_extensions]
                image_old = cv2.imread(os.path.join(dir_path,image_list[0]))
                for image_file in image_list[1:]:
                    current_image_path = os.path.join(dir_path, image_file)
                    image = cv2.imread(current_image_path)
                    _, _, cnts, score= self.compare_frame(image_old, image)
                    if(len(cnts) == 0 or score >= 0.99): 
                        print(f"Deleting: {current_image_path}")
                        os.remove(current_image_path)
                    image_old = image.copy()
                self.rename_images(dir_path)

