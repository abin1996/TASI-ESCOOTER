import pandas as pd
import datetime
import numpy as np
import os
import shutil
import re

joystick_button_type_dict = {
    '[0 1 0 0 0 0 0 0 0 0 0 0]': 'escooter',
    '[0 0 1 0 0 0 0 0 0 0 0 0]': 'bike',
}

def convert_click(click_file_dir):
    with open(click_file_dir) as f:
        contents = f.readlines()
    timestamp = []
    buttons = []
    direction_b = []
    for i in range(0, len(contents), 9):
        timestamp.append(int(contents[i+3].split(':')[-1]))
        buttons.append(eval(contents[i+7].split(':')[-1]))
        direction_b.append((contents[i+6].split(':')[-1]))

    buttons = np.asarray(buttons)
    direction_b = np.asarray(direction_b)

    df_click = pd.DataFrame()
    df_click['click_timestamp'] = timestamp
    df_click['click_timestamp_readable'] = [str(datetime.datetime.fromtimestamp(i)) for i in timestamp]
    df_click['button'] = list(buttons)
    types = [joystick_button_type_dict.get(str(i), 'unknown click') for i in df_click.button]
    df_click['button_type'] = types
    return df_click

def add_frames(f_click, before, after):
    f_click['frame_start_time'] = f_click['click_timestamp'] - before
    f_click['frame_end_time'] = f_click['click_timestamp'] + after
    f_click['frame_start_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_start_time']]
    f_click['frame_end_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_end_time']]
    return f_click

def add_scenario(f_click):
    scenario_number = 1
    f_click['scenario'] = scenario_number
    n = len(f_click)
    
    for i in range(1, n):
        current_start_time = f_click.iloc[i]['frame_start_time']
        previous_end_time = f_click.iloc[i-1]['frame_end_time']
        
        if not np.isnan(current_start_time) and not np.isnan(previous_end_time):
            if current_start_time > previous_end_time:
                scenario_number += 1
                f_click.iloc[i, f_click.columns.get_loc('scenario')] = scenario_number
            else:
                # Ensure the current event is merged into the previous scenario
                f_click.iloc[i, f_click.columns.get_loc('scenario')] = f_click.iloc[i-1, f_click.columns.get_loc('scenario')]
                # Update the frame_end_time of the previous event if needed
                if f_click.iloc[i]['frame_end_time'] > previous_end_time:
                    f_click.iloc[i-1, f_click.columns.get_loc('frame_end_time')] = f_click.iloc[i]['frame_end_time']
        else:
            f_click.iloc[i, f_click.columns.get_loc('scenario')] = scenario_number
    
    return f_click


def generate_scenario_summary(df):
    scenario_summary = df.groupby('scenario').agg(
        start_time=('frame_start_time', 'min'),
        end_time=('frame_end_time', 'max'),
        start_time_readable=('frame_start_time_readable', 'min'),
        end_time_readable=('frame_end_time_readable', 'max'),
        escooter_clicks=('button_type', lambda x: (x == 'escooter').sum()),
        bike_clicks=('button_type', lambda x: (x == 'bike').sum()),
        pedestrian_clicks=('button_type', lambda x: (x == 'pedestrian').sum())
    ).reset_index()
    return scenario_summary

def count_successive_button_pattern_matches(entries):
    escooter_count = 0
    bike_count = 0
    pedestrian_count = 0

    i = 1
    while i < len(entries):
        if np.array_equal(entries[i][1], entries[i-1][1]) and abs(entries[i][0] - entries[i-1][0]) <= 2:
            button_pattern = entries[i][1]
            if button_pattern[1] == 1:
                escooter_count += 1
            elif button_pattern[2] == 1:
                bike_count += 1
            elif button_pattern[0] == 1:
                pedestrian_count += 1
            i += 1  # Skip the next entry if a match is found
        i += 1

    return escooter_count, bike_count, pedestrian_count

def scenario_sort(input_file, folder_name):
    df_click = convert_click(input_file)
    frame_periods = [(20, 20), (10, 10), (5, 5), (7,7), (2, 13)]  # (before, after)
    summaries = []

    for before, after in frame_periods:
        df_click = df_click[
            (df_click['button_type'] != 'unknown click')
        ]
        
        df_click_period = add_frames(df_click.copy(), before, after)
        df_click_period = add_scenario(df_click_period)
        df_click_period = df_click_period.dropna(subset=['frame_start_time', 'frame_end_time'])
        print(df_click_period)
        
        df_new = generate_scenario_summary(df_click_period)
        df_new['duration(s)'] = df_new['end_time'] - df_new['start_time']
        df_new['folder'] = folder_name
        
        # Prepare the entries for the successive pattern match counting
        entries = list(zip(df_click_period['click_timestamp'], df_click_period['button']))
        escooter_count, bike_count, pedestrian_count = count_successive_button_pattern_matches(entries)

        # Save dataframe to CSV
        period_label = f'{before}_{after}'
        df_new.to_csv(f'joystick_clicks_period_{period_label}.csv', index=False)
        # Open output file for writing
        with open(f'output_period_{period_label}.txt', 'w') as output_file:
            output_file.write(f"Period: {period_label}\n")
            output_file.write("Number of scenarios: {}\n".format(df_click_period['scenario'].nunique()))
            output_file.write("Number of ESCOOTER clicks: {}\n".format(escooter_count))
            output_file.write("Number of BIKE clicks: {}\n".format(bike_count))
            output_file.write("Number of PEDESTRIAN clicks: {}\n".format(pedestrian_count))
            output_file.write("Total Duration = {} seconds\n".format(sum(df_new['duration(s)'])))

        # Append summary data for final report
        summaries.append({
            'period': period_label,
            'num_scenarios': df_click_period['scenario'].nunique(),
            'CB_Scenario Total Duration(s)': sum(df_new['duration(s)']),
        })

    # Generate final summary report
    final_summary = pd.DataFrame(summaries)
    final_summary.to_csv('CBS_summary.csv', index=False)

    print("CSV files generated successfully!")
    return 0

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
    joystick_files = find_joystick_files()

    for input_file in joystick_files:
        folder_name = os.path.basename(os.path.dirname(os.path.dirname(input_file)))
        output_folder = os.path.dirname(input_file)
        os.makedirs(output_folder, exist_ok=True)
        scenario_sort(input_file, folder_name)
        # Move generated files to output subfolder
        output_files = ['joystick_clicks_period_{}.csv'.format(period) for period in ['20_20', '10_10', '5_5', '7_7', '2_13']] + ['output_period_{}.txt'.format(period) for period in ['20_20', '10_10', '5_5', '7_7','2_13']]
        output_files.append('CBS_summary.csv')
        for output_file in output_files:
            shutil.move(output_file, os.path.join(output_folder, output_file))

# Entry point of the script
process_all_joystick_files()
