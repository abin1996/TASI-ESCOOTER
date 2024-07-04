import os
import shutil

# Hardcoded paths
MAIN_FOLDER = '/mnt/TASI-VRU2/Extracted_Object_Based_Scenarios'  # Update this path
DEST_FOLDER = '/media/abinmath/TASI-ESC-OBS-BAC/Object_Based_Scenarios_Backup/Data_2022'  # Update this path

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def calculate_sizes(main_folder):
    print("Starting size calculation...")
    parent_folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f)) and '_' in f]
    total_sizes = {}
    grand_total_size = 0

    for idx, parent in enumerate(parent_folders, start=1):
        parent_path = os.path.join(main_folder, parent)
        parent_size = 0
        
        for child in os.listdir(parent_path):
            child_path = os.path.join(parent_path, child)
            if os.path.isdir(child_path):
                # Consider only "1fps" subfolder and "sync_sce.csv" file
                fps_folder = os.path.join(child_path, '1fps')
                sync_file = os.path.join(child_path, 'sync_sce.csv')

                if os.path.isdir(fps_folder):
                    parent_size += get_size(fps_folder)

                if os.path.isfile(sync_file):
                    parent_size += os.path.getsize(sync_file)

        size_gb = parent_size / (1024 ** 3)
        print(f"{idx}. Total size of {parent}: {parent_size} bytes ({size_gb:.2f} GB)")
        total_sizes[parent] = parent_size
        grand_total_size += parent_size

    print("Size calculation completed.")
    return total_sizes, grand_total_size

def copy_files(main_folder, dest_folder):
    parent_folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f)) and '_' in f]

    for parent in parent_folders:
        parent_path = os.path.join(main_folder, parent)
        dest_parent_path = os.path.join(dest_folder, parent)
        os.makedirs(dest_parent_path, exist_ok=True)
        print(f"Copying parent folder: {parent}")
        for child in os.listdir(parent_path):
            child_path = os.path.join(parent_path, child)
            if os.path.isdir(child_path):
                fps_folder = os.path.join(child_path, '1fps')
                sync_file = os.path.join(child_path, 'sync_sce.csv')

                if os.path.isdir(fps_folder):
                    dest_fps_folder = os.path.join(dest_parent_path, child, '1fps')
                    os.makedirs(os.path.dirname(dest_fps_folder), exist_ok=True)
                    shutil.copytree(fps_folder, dest_fps_folder)

                if os.path.isfile(sync_file):
                    dest_sync_file = os.path.join(dest_parent_path, child, 'sync_sensor_timestamps.csv')
                    os.makedirs(os.path.dirname(dest_sync_file), exist_ok=True)
                    shutil.copy2(sync_file, dest_sync_file)

        print(f"Copied parent folder: {parent}")
        print(f'Remaining parent folders: {len(parent_folders) - parent_folders.index(parent) - 1}')

def copy_files_full_ob(main_folder, dest_folder):
    parent_folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f)) and '_' in f]

    for parent in parent_folders:
        parent_path = os.path.join(main_folder, parent)
        dest_parent_path = os.path.join(dest_folder, parent)
        # os.makedirs(dest_parent_path, exist_ok=True)
        print(f"Copying parent folder: {parent}")
        shutil.copytree(parent_path, dest_parent_path)

        print(f"Copied parent folder: {parent}")
        print(f'Remaining parent folders: {len(parent_folders) - parent_folders.index(parent) - 1}')

def calculate_sizes_full_ob(main_folder):
    print("Starting size calculation...")
    parent_folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f)) and '_' in f]
    total_sizes = {}
    grand_total_size = 0

    for idx, parent in enumerate(parent_folders, start=1):
        parent_path = os.path.join(main_folder, parent)
        parent_size = 0
        
        if os.path.isdir(parent_path):
            parent_size += get_size(parent_path)


        size_gb = parent_size / (1024 ** 3)
        print(f"{idx}. Total size of {parent}: {parent_size} bytes ({size_gb:.2f} GB)")
        total_sizes[parent] = parent_size
        grand_total_size += parent_size

    print("Size calculation completed.")
    return total_sizes, grand_total_size

def main():
    # total_sizes, grand_total_size = calculate_sizes_full_ob(MAIN_FOLDER)

    # grand_total_size_gb = grand_total_size / (1024 ** 3)
    # print(f"Grand total size of the main folder: {grand_total_size} bytes ({grand_total_size_gb:.2f} GB)")

    copy = input("Do you want to copy these folders/files to the destination? (y/n): ")
    if copy.lower() == 'y':
        copy_files_full_ob(MAIN_FOLDER, DEST_FOLDER)
        print("Files and folders have been copied successfully.")

if __name__ == "__main__":
    main()
