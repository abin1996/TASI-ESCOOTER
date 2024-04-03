import pandas as pd
import datetime
import numpy as np

joystick_button_type_dict={
'[0 0 0 0 0 0 0 0 0 0 0]': 'back_click',
'[1 0 0 0 0 0 0 0 0 0 0]': 'escooter',
'[0 0 1 0 0 0 0 0 0 0 0]': 'bike',
'[0 1 0 0 0 0 0 0 0 0 0]': 'pedestrian',
'[0 0 0 1 0 0 0 0 0 0 0]': 'interesting',
'[0 0 0 0 1 0 0 0 0 0 0]': 'can_ignore'
}

def convert_click(click_file_dir):
  with open(click_file_dir) as f:
    contents = f.readlines()
  timestamp = []
  buttons = []
  direction_b = []
#   print(contents)
  for i in range(0,len(contents),9):
    timestamp.append(int(contents[i+3].split(':')[-1]))
    buttons.append(eval(contents[i+7].split(':')[-1]))
    direction_b.append((contents[i+6].split(':')[-1]))
    #print(contents[i+3])

  buttons =np.asarray(buttons)
  direction_b = np.asarray(direction_b)

  df_click = pd.DataFrame()
  df_click['click_timestamp'] = timestamp
  df_click['click_timestamp_readable']=[str(datetime.datetime.fromtimestamp(i)) for i in timestamp]
  df_click['button']=list(buttons)
  types=[]
  for i in df_click.button:
    types.append(joystick_button_type_dict.get(str(i),'unknown click'))
  df_click['button_type']=types
#   print(df_click)
  return df_click
def add_frames(f_click, p):
    f_click['frame_start_time'] = f_click['click_timestamp'] - p
    f_click['frame_end_time'] = f_click['click_timestamp'] + p
    f_click['frame_start_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_start_time']]
    f_click['frame_end_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_end_time']]
    return f_click
def add_scenario(f_click):
    scenario_number = 1
    f_click['scenario'] = 0
    n = len(f_click)
    for i in range(1, n):
        if f_click.iloc[i]['frame_start_time'] >= f_click.iloc[i-1]['frame_end_time']:
            scenario_number += 1
        f_click.at[i, 'scenario'] = scenario_number
    return f_click
def generate_scenario_summary(df):
    scenario_summary = df.groupby('scenario').agg(
        start_time=('frame_start_time', 'min'),
        end_time=('frame_end_time', 'max'),
        start_time_readable=('frame_start_time_readable','min'),
        end_time_readable=('frame_end_time_readable','max'),
        escooter_clicks=('button_type', lambda x: (x == 'escooter').sum()),
        bike_clicks=('button_type', lambda x: (x == 'bike').sum()),
        pedestrian_clicks=('button_type', lambda x: (x == 'pedestrian').sum())
    ).reset_index()
    return scenario_summary
df_click = convert_click('01-08-22_16-42-13.txt')
frame_periods = [20, 10, 5, 7]
videotimestamps = open('images1_timestamps.txt')
videostart = int(videotimestamps.readline())
videotimestamps.close()
for i, period in enumerate(frame_periods, start=1):
    df_click_period = add_frames(df_click.copy(), period)
    df_click_period = add_scenario(df_click_period)
    df_click_period = df_click_period[(df_click_period['button_type'] != 'back_click') &
                                      (df_click_period['button_type'] != 'can_ignore') &
                                      (df_click_period['button_type'] != 'interesting') &
                                      (df_click_period['button_type'] != 'unknown click')]
    df_new = generate_scenario_summary(df_click_period)
    df_new['duration(s)'] = df_new['end_time'] - df_new['start_time']
    df_new['video_start_time'] = df_new['start_time'] - videostart
    df_new['video_end_time'] = df_new['end_time'] - videostart
    #df_new['video_start_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in df_new['video_start_time']]
    #df_new['video_end_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in df_new['video_end_time']]
    # Save dataframe to CSV
    df_new.to_csv(f'joystick_clicks_period_{period}.csv', index=False)
    # Open output file for writing
    with open(f'output_period_{period}.txt', 'w') as output_file:
      output_file.write(f"Period: {period}\n")
      output_file.write("Number of scenarios: {}\n".format(df_click_period['scenario'].nunique()))
      output_file.write("Number of ESCOOTER clicks: {}\n".format(len(df_click_period[df_click_period['button_type'] == 'escooter'])))
      output_file.write("Number of BIKE clicks: {}\n".format(len(df_click_period[df_click_period['button_type'] == 'bike'])))
      output_file.write("Number of PEDESTRIAN clicks: {}\n".format(len(df_click_period[df_click_period['button_type'] == 'pedestrian'])))
      output_file.write("Total Duration = {} seconds\n".format(sum(df_new['duration(s)'])))
      output_file.close()
print("CSV files generated successfully!")