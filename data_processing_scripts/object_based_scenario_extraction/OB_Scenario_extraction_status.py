import os
import csv
from datetime import datetime

def get_city_from_date(date_str):
    date = datetime.strptime(date_str, "%d-%m-%y")
    if date.month == 5 and date.year == 2022:
        return "Austin"
    if datetime.strptime("15-06-22", "%d-%m-%y") <= date <= datetime.strptime("10-07-22", "%d-%m-%y"):
        return "San Diego"
    if datetime.strptime("25-07-22", "%d-%m-%y") <= date <= datetime.strptime("10-08-22", "%d-%m-%y"):
        return "Boston"
    if date_str in ["19-07-22", "20-07-22", "21-07-22", "18-08-22", "19-08-22", "20-08-22"]:
        return "Indianapolis"
    return "city_error"

def determine_extraction_status(folder_path):
    total_items = len(os.listdir(folder_path))
    if total_items == 0:
        return "Error"
    elif total_items == 11:
        return "Success"
    else:
        return "Incomplete"

def main():
    parent_folder_path = "/mnt/TASI-VRU2/Extracted_Object_Based_Scenarios/"  # Change this to your actual path
    output_csv_path = "/home/dp75@ads.iu.edu/TASI/OB Scenario/Result/OB_Scenario_Status.csv"  # Change this to your desired output path

    # List to store the results
    results = []
    index = 1

    # Counters for statuses
    total_healthy = 0
    total_error = 0
    total_incomplete = 0
    total_scenarios = 0

    # Walk through the directories in the parent folder
    for root, dirs, files in os.walk(parent_folder_path):
        for dir_name in dirs:
            if "_" in dir_name and "-" in dir_name:
                main_folder_path = os.path.join(root, dir_name)
                date_part = dir_name.split("_")[0]

                # Counters for each folder
                folder_healthy = 0
                folder_error = 0
                folder_incomplete = 0
                folder_scenarios = 0

                for sub_root, sub_dirs, sub_files in os.walk(main_folder_path):
                    for sub_dir_name in sub_dirs:
                        if "_" in sub_dir_name:
                            scenario_folder_path = os.path.join(sub_root, sub_dir_name)
                            extraction_status = determine_extraction_status(scenario_folder_path)
                            city_name = get_city_from_date(date_part)

                            results.append({
                                "Index": index,
                                "Raw_data_folder": sub_dir_name,
                                "City_name": city_name,
                                "Extraction_status": extraction_status
                            })

                            index += 1
                            folder_scenarios += 1

                            if extraction_status == "Success":
                                folder_healthy += 1
                            elif extraction_status == "Error":
                                folder_error += 1
                            else:
                                folder_incomplete += 1

                # Print status for each main folder
                print(f"Folder: {dir_name}")
                print(f"  Healthy: {folder_healthy}")
                print(f"  Error: {folder_error}")
                print(f"  Incomplete: {folder_incomplete}")

                total_healthy += folder_healthy
                total_error += folder_error
                total_incomplete += folder_incomplete
                total_scenarios += folder_scenarios

    # Print grand totals
    print("Grand Totals")
    print(f"  Healthy: {total_healthy}")
    print(f"  Error: {total_error}")
    print(f"  Incomplete: {total_incomplete}")
    print(f"  Total Scenarios: {total_scenarios}")

    # Define CSV headers
    headers = ["Index", "Raw_data_folder", "City_name", "Extraction_status"]

    # Write results to CSV
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"CSV file saved to {output_csv_path}")

if __name__ == "__main__":
    main()
