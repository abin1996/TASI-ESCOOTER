import re

def parse_entries(content):
    """Parses the content of the file into a list of dictionaries with the button values."""
    entries = []
    entry_pattern = re.compile(r'header:.*?buttons:\s*\[(.*?)\]', re.DOTALL)
    matches = entry_pattern.findall(content)
    
    for match in matches:
        # Convert the button string to a list of integers
        buttons = list(map(int, match.split(',')))
        entries.append(buttons)
    
    return entries

def count_successive_button_pattern_matches(entries):
    """Counts the occurrences where successive entries have the same button pattern."""
    escooter_count = 0
    bicycle_count = 0

    for i in range(1, len(entries)):
        if entries[i] == entries[i-1]:
            if entries[i][1] == 1:
                escooter_count += 1
            elif entries[i][2] == 1:
                bicycle_count += 1

    return escooter_count, bicycle_count

def write_output(escooter_count, bicycle_count, output_file):
    """Writes the counts of escooters and bicycles to the output file."""
    with open(output_file, 'w') as file:
        file.write(f'Number of escooters: {escooter_count}\n')
        file.write(f'Number of bicycles: {bicycle_count}\n')
        file.write(f'Number of VRUs: {escooter_count + bicycle_count}\n')

def main(input_file, output_file):
    with open(input_file, 'r') as file:
        content = file.read()

    entries = parse_entries(content)
    escooter_count, bicycle_count = count_successive_button_pattern_matches(entries)
    write_output(escooter_count, bicycle_count, output_file)

input_file = 'joystick_2024-05-29_15-06-03.txt'
output_file = 'click_counter_joystick_2024-05-29_15-06-03.txt'
main(input_file, output_file)

