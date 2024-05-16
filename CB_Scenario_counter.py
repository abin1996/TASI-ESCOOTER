import os
import pandas as pd

class ScenarioProcessor:
    def __init__(self, source_joy_click_folder, scenario_dir, checked_folders_file):
        self.source_joy_click_folder = source_joy_click_folder
        self.scenario_dir = scenario_dir
        self.checked_folders_file = checked_folders_file
        self.count = 0
        self.data_ready = []
        self.scenarios_count = 0
        self.checked_folders = self.load_checked_folders()
        print(self.checked_folders)

    def load_checked_folders(self):
        if os.path.exists(self.checked_folders_file):
            with open(self.checked_folders_file, 'r') as file:
                return [line.strip() for line in file]
        return []

    def get_city_name(self, folder_name):
        video_date = folder_name.split('_')[0]
        date = int(video_date.split('-')[0])
        month = int(video_date.split('-')[1])
        if month == 5:
            if 1 <= date <= 31:
                return "austin"
        if (month == 6 and 1 <= date <= 15) or (month == 7 and 1 <= date <= 2):
            return "san_diego"
        if (month == 7 and 25 <= date <= 31) or (month == 8 and 1 <= date <= 10):
            return "boston"
        return "indy"

    def process_folders(self, target_city):
        list_of_folders = os.listdir(self.scenario_dir)
        if 'Local Disk (C) - Shortcut.lnk' in list_of_folders:
            list_of_folders.remove('Local Disk (C) - Shortcut.lnk')
        for raw_data_folder in list_of_folders:
            print(f"Starting to check folder: {raw_data_folder}")
            self.count += len(os.listdir(os.path.join(self.scenario_dir, raw_data_folder)))
            city = self.get_city_name(raw_data_folder)
            if city != target_city:
                continue
            if raw_data_folder in self.checked_folders:
                # print(f"{raw_data_folder} is already checked.")
                continue
            
            
            self.scenarios_count = len(os.listdir(os.path.join(self.scenario_dir, raw_data_folder)))
            joystick_click_csv_path = os.path.join(self.source_joy_click_folder, raw_data_folder, "joystick_clicks_period_20.csv")
            joystick_click_csv = pd.read_csv(joystick_click_csv_path)
            if 'status' not in joystick_click_csv.columns:
                # print(f"{raw_data_folder} is currently being processed by CB extraction.")
                continue
            print(f"Processing folder: {raw_data_folder}")
            if joystick_click_csv['status'].iloc[-1] == 'Done':
                print(f"All scenarios processed for this folder: {raw_data_folder}")
                self.data_ready.append(raw_data_folder)
                if len(joystick_click_csv) != self.scenarios_count:
                    print(f"Some scenarios are missing due to errors. Check the csv file: {joystick_click_csv_path}")
            else:
                # print(f"{raw_data_folder} is currently being processed by CB extraction.")
                continue

    def save_ready_folders(self, output_file):
        with open(output_file, "w") as file:
            for folder in self.data_ready:
                file.write(folder + "\n")
        print(f"Total Number of CB scenarios: {self.count}")
        print(f"Data Ready for {len(self.data_ready)} folders: {self.data_ready}")

# Usage
source_joy_click_folder = '/mnt/TASI-VRU1/click_based_scenarios_joy_csv'
scenario_dir = '/mnt/TASI-VRU2/Extracted_Click_Based_Scenarios'
checked_folders_file = '/home/abinmath@ads.iu.edu/TASI-ESCOOTER/CB_Scenario_loaded_in_excel.txt'
output_file = '/home/abinmath@ads.iu.edu/TASI-ESCOOTER/CB_Scenario_folders_ready_austin.txt'
target_city = 'austin'

processor = ScenarioProcessor(source_joy_click_folder, scenario_dir, checked_folders_file)
processor.process_folders(target_city)
processor.save_ready_folders(output_file)
