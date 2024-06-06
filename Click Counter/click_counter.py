import re
import os
import pandas as pd

def parse_entries(content):
    """Parses the content of the file into a list of tuples with secs value and button arrays."""
    entries = []
    entry_pattern = re.compile(r'secs:\s*(\d+).*?buttons:\s*\[(.*?)\]', re.DOTALL)
    matches = entry_pattern.findall(content)
    
    for match in matches:
        secs = int(match[0])
        buttons = list(map(int, match[1].split(',')))
        if any(buttons):  # Only add non-zero patterns
            entries.append((secs, buttons))
    return entries

def count_successive_button_pattern_matches(entries):
    """Counts the occurrences where successive entries have the same button pattern within a time difference of 2 seconds."""
    escooter_count = 0
    bicycle_count = 0

    for i in range(1, len(entries)):
        if entries[i][1] == entries[i-1][1] and abs(entries[i][0] - entries[i-1][0]) <= 1:
            if entries[i][1][1] == 1:
                escooter_count += 1
            elif entries[i][1][2] == 1:
                bicycle_count += 1

    return escooter_count, bicycle_count

def write_output(escooter_count, bicycle_count, filename, output_file):
    """Writes the counts of escooters, bicycles, and the total to the output file."""
    total_count = escooter_count + bicycle_count
    with open(output_file, 'a') as file:
        file.write(f'Filename: {filename}\n')
        file.write(f'Number of escooters: {escooter_count}\n')
        file.write(f'Number of bicycles: {bicycle_count}\n')
        file.write(f'Total number: {total_count}\n')

def process_file(input_file):
    with open(input_file, 'r') as file:
        content = file.read()

    entries = parse_entries(content)
    escooter_count, bicycle_count = count_successive_button_pattern_matches(entries)
    
    # Extract filename
    filename = os.path.basename(input_file)
    filename = re.search(r'(?<=joystick_)[^\\]*(?=.txt)', filename).group()
    
    # Construct output file path
    output_file = os.path.splitext(input_file)[0] + '_click_counter.txt'
    
    write_output(escooter_count, bicycle_count, filename, output_file)
    
    return filename, escooter_count, bicycle_count, escooter_count + bicycle_count

def process_file_list(file_list_path, excel_output_file):
    results = []

    if os.path.isfile(excel_output_file):
        # Load existing Excel file
        df_existing = pd.read_excel(excel_output_file)
        results = df_existing.values.tolist()

    with open(file_list_path, 'r') as file:
        input_files = file.readlines()
    
    for input_file in input_files:
        input_file = input_file.strip()  # Remove any surrounding whitespace/newlines
        if os.path.isfile(input_file):
            result = process_file(input_file)
            results.append(result)
        else:
            print(f"File {input_file} does not exist.")

    # Create DataFrame and write to Excel
    df = pd.DataFrame(results, columns=['Filename', 'Number of Escooters', 'Number of Bicycles', 'Total Number'])
    df.to_excel(excel_output_file, index=False)

# Entry point of the script
file_list_path = 'C:/Users/LENOVO/Downloads/joystick_files_to_be_processed.txt'
excel_output_file = 'C:/Users/LENOVO/Downloads/joystick_click_counter_summary.xlsx'
process_file_list(file_list_path, excel_output_file)
