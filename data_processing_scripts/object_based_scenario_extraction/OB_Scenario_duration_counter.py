import os
import pandas as pd
from datetime import datetime

def convert_time(timestamp):
    try:
        return datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error converting timestamp {timestamp}: {e}")
        return "Invalid timestamp"

def main(folder_path):
    results = []

    for root, dirs, files in os.walk(folder_path):
        for dir_name in dirs:
            csv_file_path = os.path.join(root, dir_name, "object_based_scenarios.csv")
            if os.path.exists(csv_file_path):
                try:
                    df = pd.read_csv(csv_file_path)
                    if df.empty:
                        print(f"CSV file in {dir_name} is empty.")
                        continue

                    total_duration_seconds = 0

                    for index, row in df.iterrows():
                        start_time = row[1]
                        stop_time = row[2]

                        start_time_readable = convert_time(start_time)
                        stop_time_readable = convert_time(stop_time)
                        duration_seconds = float(stop_time) - float(start_time)
                        duration_minutes = duration_seconds / 60

                        total_duration_seconds += duration_seconds

                        results.append({
                            "Folder Name": dir_name,
                            "Start Time": start_time_readable,
                            "Stop Time": stop_time_readable,
                            "Duration (seconds)": duration_seconds,
                            "Duration (minutes)": duration_minutes
                        })

                    # Add total duration for the CSV file
                    total_duration_minutes = total_duration_seconds / 60
                    results.append({
                        "Folder Name": dir_name,
                        "Start Time": "Total",
                        "Stop Time": "Total",
                        "Duration (seconds)": total_duration_seconds,
                        "Duration (minutes)": total_duration_minutes  
                    })

                except Exception as e:
                    print(f"Error processing file {csv_file_path}: {e}")

    if results:
        print("\n")
        print("{:<20} {:<20} {:<20} {:<20} {:<20}".format(
            "Folder Name", "Start Time", "Stop Time", "Duration (seconds)", "Duration (minutes)"
        ))
        for result in results:
            print("{:<20} {:<20} {:<20} {:<20} {:<20}".format(
                result["Folder Name"],
                result["Start Time"],
                result["Stop Time"],
                f"{result['Duration (seconds)']:.2f}",
                f"{result['Duration (minutes)']:.2f}"
            ))
    else:
        print("No valid data found.")

if __name__ == "__main__":
    folder_path = input("Enter the path to the main folder: ")
    main(folder_path)
