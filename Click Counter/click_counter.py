import re

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

def write_output(escooter_count, bicycle_count, output_file):
    """Writes the counts of escooters, bicycles, and the total to the output file."""
    total_count = escooter_count + bicycle_count
    with open(output_file, 'w') as file:
        file.write(f'Number of escooters: {escooter_count}\n')
        file.write(f'Number of bicycles: {bicycle_count}\n')
        file.write(f'Total number: {total_count}\n')

def main(input_file, output_file):
    with open(input_file, 'r') as file:
        content = file.read()

    entries = parse_entries(content)
    escooter_count, bicycle_count = count_successive_button_pattern_matches(entries)
    write_output(escooter_count, bicycle_count, output_file)

input_file = 'joystick_2024-06-03_16-06-37.txt'
output_file = 'click_counter_joystick_2024-06-03_16-06-37.txt'
main(input_file, output_file)
