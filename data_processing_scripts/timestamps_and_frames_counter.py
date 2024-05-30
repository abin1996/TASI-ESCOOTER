import os
import csv
import cv2

def count_timestamps(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return len(lines)

def count_video_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return frame_count

def main():
    parent_folder_path = "/mnt/TASI-VRU1/Reordered_drive/Raw_Data/"  # Change this to your actual path
    output_csv_path = "/home/dp75@ads.iu.edu/TASI/OB Scenario/Result/output.csv"  # Change this to your desired output path

    # List to store the results
    results = []

    # Index for results
    index = 1

    # Counter for processed folders
    processed_folder_count = 0

    # Walk through the directories in the parent folder
    for root, dirs, files in os.walk(parent_folder_path):
        for dir_name in dirs:
            if "_" in dir_name and "-" in dir_name:
                processed_folder_path = os.path.join(root, dir_name, "processed")
                if os.path.exists(processed_folder_path):
                    timestamps_folder_path = os.path.join(processed_folder_path, "timestamps")
                    videos_folder_path = os.path.join(processed_folder_path, "videos")

                    image_data = {}
                    for i in range(1, 7):
                        timestamps_file_path = os.path.join(timestamps_folder_path, f"images{i}_timestamps.txt")
                        video_file_path = None
                        for video_file in os.listdir(videos_folder_path):
                            if video_file.startswith(f"images{i}_") and video_file.endswith(".mp4"):
                                video_file_path = os.path.join(videos_folder_path, video_file)
                                break

                        total_timestamps = count_timestamps(timestamps_file_path) if os.path.exists(timestamps_file_path) else 0
                        total_frames = count_video_frames(video_file_path) if video_file_path and os.path.exists(video_file_path) else 0

                        compare_value = 0
                        if total_timestamps > total_frames:
                            compare_value = 1
                        elif total_frames > total_timestamps:
                            compare_value = 2

                        image_data[f"total_timestamps_image_{i}"] = total_timestamps
                        image_data[f"total_frames_image_{i}"] = total_frames
                        image_data[f"compare_image_{i}"] = compare_value

                    results.append({
                        "Index": index,
                        "Folder Name": dir_name,
                        **image_data
                    })
                    index += 1

                    # Increment the processed folder count and print status
                    processed_folder_count += 1
                    print(f"Processed folder {processed_folder_count}: {dir_name}")

    # Define CSV headers
    headers = ["Index", "Folder Name"]
    for i in range(1, 7):
        headers.extend([
            f"total_timestamps_image_{i}",
            f"total_frames_image_{i}",
            f"compare_image_{i}"
        ])

    # Write results to CSV
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    # Print the results
    print("{:<5} {:<25} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
        "Index", "Folder Name",
        "TS_img1", "FR_img1",
        "TS_img2", "FR_img2",
        "TS_img3", "FR_img3",
        "TS_img4", "FR_img4",
        "TS_img5", "FR_img5",
        "TS_img6", "FR_img6",
        "Comp_img1", "Comp_img2", "Comp_img3", "Comp_img4", "Comp_img5", "Comp_img6"
    ))
    for result in results:
        print("{:<5} {:<25} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
            result["Index"], result["Folder Name"],
            result.get("total_timestamps_image_1", 0), result.get("total_frames_image_1", 0),
            result.get("total_timestamps_image_2", 0), result.get("total_frames_image_2", 0),
            result.get("total_timestamps_image_3", 0), result.get("total_frames_image_3", 0),
            result.get("total_timestamps_image_4", 0), result.get("total_frames_image_4", 0),
            result.get("total_timestamps_image_5", 0), result.get("total_frames_image_5", 0),
            result.get("total_timestamps_image_6", 0), result.get("total_frames_image_6", 0),
            result.get("compare_image_1", 0), result.get("compare_image_2", 0), result.get("compare_image_3", 0),
            result.get("compare_image_4", 0), result.get("compare_image_5", 0), result.get("compare_image_6", 0)
        ))

if __name__ == "__main__":
    main()
