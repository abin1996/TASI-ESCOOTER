import os
import pickle

# Replace 'your_file.pkl' with the path to your pickle file
file_path = '/Volumes/TASI-VRU Data Storage/Reordered_drive/processed_final/05-08-22_10-33-20_42274247_2_016_010/05-08-22_10-33-20_42274247_2_016_010_case_pcd_ts.pkl'

try:
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
        print("Contents of the pickle file:")
        print(data)
        # print(data['25411.0'])
        # print(len(data['bd']))
        # print(len(data['front_right'][0]))
        # for i in data['bd']:
        #     print(i)
except FileNotFoundError:
    print("File not found.")
except Exception as e:
    print("An error occurred:", e)


