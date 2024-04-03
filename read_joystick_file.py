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

df_click = convert_click('sample_joystick_file.txt')
#Comment below line if you want to keep all the clicks
df_click = df_click[(df_click['button_type']  !='back_click' )&(df_click['button_type']  !='can_ignore') &(df_click['button_type']  !='interesting') &(df_click['button_type']  !='unknown click')]
print("Number of ESCOOTER clicks: ",len(df_click[df_click['button_type']=='escooter']))
print("Number of BIKE clicks: ",len(df_click[df_click['button_type']=='bike']))
print("Number of PEDESTRIAN clicks: ",len(df_click[df_click['button_type']=='pedestrian']))
df_click.to_csv('joystick_clicks.csv',index=False)
