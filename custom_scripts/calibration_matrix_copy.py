import os
import shutil
from datetime import datetime

# Hardcoded paths
MAIN_FOLDER = '/media/pate2372/TASI-ESC-BKCP/Extracted_Object_Based_Scenarios_2024_part1'  # Update this path
CALIBRATION_MATRIX_PATH = '/home/pate2372/TASI/Work/Calibration/calibration_parameters.json'  # Update this path to the single calibration matrix

def copy_json_to_child_folders(main_folder, calibration_matrix_path):
    parent_folders = sorted([f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f)) and '_' in f])

    for idx, parent in enumerate(parent_folders, start=1):
        parent_path = os.path.join(main_folder, parent)

        for child in os.listdir(parent_path):
            child_path = os.path.join(parent_path, child)
            if os.path.isdir(child_path):
                # Copy to the child folder
                dest_json_file_path = os.path.join(child_path, "calibration_parameters.json")
                shutil.copy2(calibration_matrix_path, dest_json_file_path)

                # Copy to the 1 FPS subfolder
                fps_folder_path = os.path.join(child_path, "1FPS")
                if os.path.isdir(fps_folder_path):
                    dest_json_file_path_fps = os.path.join(fps_folder_path, "calibration_parameters.json")
                    shutil.copy2(calibration_matrix_path, dest_json_file_path_fps)

        print(f"{idx}. {parent} processed. Calibration matrix was copied.")

def main():
    copy_json_to_child_folders(MAIN_FOLDER, CALIBRATION_MATRIX_PATH)
    print("JSON files have been copied based on the specified date ranges.")

if __name__ == "__main__":
    main()
 