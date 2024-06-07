import os
import csv
from datetime import datetime

def get_city_from_date(date_str):
    date = datetime.strptime(date_str, "%d-%m-%y")
    if date.month == 5 and date.year == 2022:
        return "Austin"
    if datetime.strptime("15-06-22", "%d-%m-%y") <= date <= datetime.strptime("10-07-22"):
        return "San Diego"
    if datetime.strptime("25-07-22", "%d-%m-%y") <= date <= datetime.strptime("10-08-22"):
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

def extract_index_from_scenario_name(scenario_name):
    parts = scenario_name.split("_")
    if len(parts) > 2:
        return parts[2]
    return "unknown"

def print_table_row(row_data, column_widths):
    row = ""
    for data, width in zip(row_data, column_widths):
        row += f"{data:<{width}} | "
    print(row)

def main():
    parent_folder_path = "/mnt/TASI-VRU2/Extracted_Object_Based_Scenarios"  # Change this to your actual path
    output_csv_path = "/home/dp75@ads.iu.edu/TASI/OB Scenario/Result/OB_Scenario_Status.csv"  # Change this to your desired output path

    # List to store the results
    results = []
    index = 1

    # Counters for statuses
    grand_total_healthy = 0
    grand_total_error = 0
    grand_total_incomplete = 0
    grand_total_scenarios = 0

    headers = ["Index", "Raw_data_folder", "City_name", "Extraction_status", "Total_Success", "Total_Error", "Total_Incomplete", "Total_Scenarios", "Error_Scenarios", "Incomplete_Scenarios"]
    column_widths = [6, 25, 15, 20, 14, 12, 16, 15, 15, 20]

    # Print table header
    print_table_row(headers, column_widths)
    print("-" * (sum(column_widths) + len(headers) * 3))

    # Walk through the directories in the parent folder
    for dir_name in os.listdir(parent_folder_path):
        if "_" in dir_name and "-" in dir_name:
            main_folder_path = os.path.join(parent_folder_path, dir_name)
            if os.path.isdir(main_folder_path):
                date_part = dir_name.split("_")[0]

                # Counters for each folder
                folder_healthy = 0
                folder_error = 0
                folder_incomplete = 0
                folder_scenarios = 0
                folder_status = "Success"
                error_scenarios = []
                incomplete_scenarios = []

                for sub_dir_name in os.listdir(main_folder_path):
                    sub_dir_path = os.path.join(main_folder_path, sub_dir_name)
                    if os.path.isdir(sub_dir_path) and "_" in sub_dir_name:
                        scenario_folder_path = sub_dir_path
                        extraction_status = determine_extraction_status(scenario_folder_path)
                        city_name = get_city_from_date(date_part)

                        folder_scenarios += 1
                        scenario_index = extract_index_from_scenario_name(sub_dir_name)

                        if extraction_status == "Success":
                            folder_healthy += 1
                        elif extraction_status == "Error":
                            folder_error += 1
                            error_scenarios.append(scenario_index)
                            folder_status = "Error"
                        else:
                            folder_incomplete += 1
                            incomplete_scenarios.append(scenario_index)
                            if folder_status != "Error":
                                folder_status = "Incomplete"

                # Append folder results
                results.append({
                    "Index": index,
                    "Raw_data_folder": dir_name,
                    "City_name": city_name,
                    "Extraction_status": folder_status,
                    "Total_Success": folder_healthy,
                    "Total_Error": folder_error,
                    "Total_Incomplete": folder_incomplete,
                    "Total_Scenarios": folder_scenarios,
                    "Error_Scenarios": "_".join(error_scenarios),
                    "Incomplete_Scenarios": "_".join(incomplete_scenarios)
                })

                # Print row for each folder
                print_table_row([index, dir_name, city_name, folder_status, folder_healthy, folder_error, folder_incomplete, folder_scenarios, "_".join(error_scenarios), "_".join(incomplete_scenarios)], column_widths)

                index += 1
                grand_total_healthy += folder_healthy
                grand_total_error += folder_error
                grand_total_incomplete += folder_incomplete
                grand_total_scenarios += folder_scenarios

    # Print grand totals
    print("-" * (sum(column_widths) + len(headers) * 3))
    print_table_row(["Grand Totals", "", "", "", grand_total_healthy, grand_total_error, grand_total_incomplete, grand_total_scenarios, "", ""], column_widths)
    print('\n')

    # Write results to CSV
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
        writer.writerow({
            "Index": "Grand Totals",
            "Raw_data_folder": "",
            "City_name": "",
            "Extraction_status": "",
            "Total_Success": grand_total_healthy,
            "Total_Error": grand_total_error,
            "Total_Incomplete": grand_total_incomplete,
            "Total_Scenarios": grand_total_scenarios,
            "Error_Scenarios": "",
            "Incomplete_Scenarios": ""
        })

    print(f"CSV file saved to {output_csv_path}")

if __name__ == "__main__":
    main()
