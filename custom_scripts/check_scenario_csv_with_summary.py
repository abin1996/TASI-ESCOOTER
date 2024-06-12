import pandas as pd
import matplotlib.pyplot as plt
import os

def process_scenario_csv(scenario_csv,folder):
    scenario_df = pd.read_csv(scenario_csv)
    # scenario_longest_duration = scenario_df['duration(s)'].max()
    # print(scenario_longest_duration)
    conscise_scenario_df = scenario_df[['scenario', 'duration(s)']]
    conscise_scenario_df['folder'] = folder
    return conscise_scenario_df
def my_fmt(x):
    # print(x)
    return '{:.1f}%\n({:.0f})'.format(x, int(total*x/100))
# if __name__ == "__main__":
folder_name = '../click_based_scenarios'
duration_df = pd.DataFrame()
for folder in os.listdir(folder_name):
    folder_path = os.path.join(folder_name, folder)
    if os.path.isdir(folder_path):
        file_path = os.path.join(folder_path, "joystick_clicks_period_20.csv")
        if os.path.isfile(file_path):
            scenario_durations_df = process_scenario_csv(file_path, folder)
            # print(scenario_durations_df)
            if scenario_durations_df.empty:
                continue
            duration_df = pd.concat([duration_df, scenario_durations_df], ignore_index=True, axis=0)
            # duration_df = duration_df.append({'Scenario': file, 'Duration': scenario_duration}, ignore_index=True)
print("Duration DF shape: ", duration_df.shape)
longest_duration_scenario = duration_df[duration_df['duration(s)'] == duration_df['duration(s)'].max()]
duration_df.to_csv('click_based_scenarios_duration.csv', index=False)
# print(duration_df)
duration_freq = duration_df['duration(s)'].value_counts().sort_index()
#Make a pie chart of the frequency of scenario durations, divide the durations into 5 categories: 0-100, 100-200, 200-300, 300-400, 400 and above
bins = [0, 60, 120,300, duration_df['duration(s)'].max()]
duration_freq = pd.cut(duration_df['duration(s)'], bins=bins).value_counts().sort_index()
total = duration_freq.sum()
plt.pie(duration_freq, labels=duration_freq.index, autopct=my_fmt)

plt.ylabel('Frequency')
plt.xlabel('Scenario Duration')
plt.title('Frequency of Scenario Durations')
plt.grid(True)
plt.show()


# plt.scatter(duration_freq.values, duration_freq.index)
# plt.ylabel('Scenario Duration')
# plt.xlabel('Frequency')
# plt.title('Frequency of Scenario Durations')
# plt.grid(True)
# plt.show()
