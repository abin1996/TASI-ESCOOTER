# Image to Video Player

This Python code creates a simple image-to-video player GUI using Tkinter. It allows users to view images as frames of a video and perform various actions such as playing, pausing, jumping to specific times, and marking scenarios.

## Dependencies
- Python 3.x
- OpenCV (`cv2`)
- Pillow (`PIL`)
- pandas
- tkinter
- os
- csv
- gc

## Usage

### Running the Program
1. Run the program by executing the `main()` function.
2. Select the raw data folder containing the 'joystick_clicks' CSV files. The program is currently designed to work with the joystick_clicks_period_20.csv
3. The program will load the initial super scenario specified in the CSV file and display the first frame.

### Interface
- **Jump to Start**: Jumps to the start of the video and begins play.
- **Jump to End**: Jumps to the end of the video and begins playing in reverse.
- **Pause/Resume**: Pauses or resumes the playback.
- **Set Start Time**: Sets the start time for marking a scenario.
- **Set Stop Time**: Sets the stop time for marking a scenario.
- **Play Backwards**: Plays the video backwards.
- **Quality**: Selects whether the scenario is a "Useful Case" or not.
- **Playback Speed**: Adjusts the playback speed of the video.
- **Final Save**: Saves the marked scenarios into a dataframe.
- **Time Widget**: Shows current time in-video
- **Scenario Screen**: Shows current scenario start and stop times
  
### Marking Scenarios
1. Play the video.
2. Set the start time of a scenario using the "Set Start Time" button. If you make a mistake, you can press the button again to change the scenario start time.
3. Set the stop time of the scenario using the "Set Stop Time" button. The program will prompt you on whether your start and stop times for the current scenario are acceptable.
   If yes, it will save the values and you can move ahead. If not, you will have to re-do this specific scenario
4. Choose the quality of the scenario. If relevant VRUs (Bicyclists and Escooters) are found in the scenario, mark it as being useful. All scenarios are useful by default.
6. Click "Final Save" to save all the scenarios created.

## Functionality
- Loads images from a specified folder to simulate video playback.
- Plays, pauses, and controls the speed of video playback.
- Marks scenarios with start and stop times, and quality.
- Saves all marked scenarios to a CSV file.

