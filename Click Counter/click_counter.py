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

    i = 1
    while i < len(entries):
        if entries[i][1] == entries[i-1][1] and abs(entries[i][0] - entries[i-1][0]) <= 1:
            if entries[i][1][1] == 1:
                escooter_count += 1
            elif entries[i][1][2] == 1:
                bicycle_count += 1
            i += 1  # Skip the next entry if a match is found
        i += 1

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

def find_joystick_files():
    """Finds all joystick files in the sub-subdirectories named 'joystick' within the current directory."""
    current_dir = os.getcwd()
    joystick_files = []
    
    for subdir in os.listdir(current_dir):
        subdir_path = os.path.join(current_dir, subdir)
        if os.path.isdir(subdir_path):
            joystick_subdir = os.path.join(subdir_path, 'joystick')
            if os.path.isdir(joystick_subdir):
                joystick_file = f'joystick_{subdir}.txt'
                joystick_file_path = os.path.join(joystick_subdir, joystick_file)
                if os.path.isfile(joystick_file_path):
                    joystick_files.append(joystick_file_path)
    return joystick_files

def process_all_joystick_files():
    results = []

    script_dir = os.path.dirname(os.path.realpath(__file__))
    excel_output_file = os.path.join(script_dir, 'joystick_click_counter_summary.xlsx')

    if os.path.isfile(excel_output_file):
        # Load existing Excel file
        df_existing = pd.read_excel(excel_output_file)
        results = df_existing.values.tolist()

    joystick_files = find_joystick_files()
    
    for input_file in joystick_files:
        result = process_file(input_file)
        results.append(result)

    # Create DataFrame and write to Excel
    df = pd.DataFrame(results, columns=['Filename', 'Number of Escooters', 'Number of Bicycles', 'Total Number'])
    df.to_excel(excel_output_file, index=False)

# Entry point of the script
process_all_joystick_files()
