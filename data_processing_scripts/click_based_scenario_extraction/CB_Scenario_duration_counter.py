import os
import pandas as pd

def main():
    # Hardcoded parent folder path
    parent_folder_path = "/mnt/TASI-VRU1/click_based_scenarios_joy_csv"  # Change this to your actual path

    # Counter for indexing the results
    index = 1

    # List to store the results
    results = []

    # Walk through the directories in the parent folder
    for root, dirs, files in os.walk(parent_folder_path):
        for dir_name in dirs:
            # Check if the folder name matches the expected pattern (Date-month-year_hour-min-sec)
            if "_" in dir_name and "-" in dir_name:
                folder_path = os.path.join(root, dir_name)
                csv_file_path = os.path.join(folder_path, "joystick_clicks_period_20.csv")
                if os.path.exists(csv_file_path):
                    try:
                        df = pd.read_csv(csv_file_path)
                        if "duration(s)" in df.columns:
                            total_duration = df["duration(s)"].sum()
                            results.append({
                                "Index": index,
                                "Folder Name": dir_name,
                                "Total Duration (seconds)": total_duration
                            })
                            index += 1
                        else:
                            print(f"Column 'duration(s)' not found in {csv_file_path}")
                    except Exception as e:
                        print(f"Error processing file {csv_file_path}: {e}")

    # Print the results
    if results:
        print("{:<5} {:<25} {:<10}".format("Index", "Folder Name", "Total Duration (seconds)"))
        for result in results:
            print("{:<5} {:<25} {:<10}".format(
                result["Index"],
                result["Folder Name"],
                f"{result['Total Duration (seconds)']:.2f}"
            ))
    else:
        print("No valid data found.")

if __name__ == "__main__":
    main()
