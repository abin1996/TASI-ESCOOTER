import os

# Set the path to the directory containing the scenario files
scenario_dir = '/mnt/TASI-VRU2/Extracted_Click_Based_Scenarios'

count = 0
for raw_data_folder in os.listdir(scenario_dir):
    #Count the number of scenarios in the folder
    count += len(os.listdir(os.path.join(scenario_dir, raw_data_folder))) - 1
print("Number of scenarios: " + str(count) + "\n")