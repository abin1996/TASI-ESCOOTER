import tkinter as tk    #IMPORTS
from tkinter import filedialog, messagebox, IntVar, W, CENTER, StringVar, OptionMenu
import cv2
from PIL import Image, ImageTk
import os
import csv
import gc
import pandas as pd
class VideoPlayer:
    def __init__(self, master, inputfolder, super_sen_num, super_sen_start_time, super_sen_end_time):   #Initialize VideoPlayer
        self.master = master
        self.master.title("Image to Video Player")
        self.master.geometry("800x700") #Size of Window. Adjusted for PC Screen, Change if code is used on a different screen

        self.image_folder_path = None   #Path to the frames/images for playback
        self.image_files = []   #List of image files
        self.current_frame_index = 0    #index keeping track of current frame
        self.video_label = tk.Label(self.master)    #initialize video with tkinter
        self.video_label.pack() #pack() is a method of arranging things on the screen, in this case the video

        self.time_label = tk.Label(self.master, text="00:00")   #Initialize a Time Label keeping track of the time from the beginning of the video
        self.time_label.pack(pady=10)

        self.track_text = tk.Text(self.master, height=5, width=60)  #Text box where users can see current and previous tracking information
        self.track_text.pack(pady=10)

        button_frame = tk.Frame(self.master)    #Frame for all buttons
        button_frame.pack(pady=10)

        #open_button = tk.Button(button_frame, text="Open Folder", command=self.scenario_iterator)
        #open_button.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(button_frame, text = "Jump to Start", command = self.start_video) #Button to play the video from the start
        self.start_button.pack(side=tk.LEFT, padx=10)

        #self.play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        #self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)   #Button to pause or resume the video playback
        self.pause_button.pack(side=tk.LEFT, padx=10)

        #stop_button = tk.Button(button_frame, text="Restart", command=self.stop_video)
        #stop_button.pack(side=tk.LEFT, padx=10)

        self.start_track_button = tk.Button(button_frame, text="Set Start Time", command=self.start_track)  #Button to start tracking a new scenario
        self.start_track_button.pack(side=tk.LEFT, padx=10)

        self.stop_track_button = tk.Button(button_frame, text="Set Stop Time", command=self.stop_track, state=tk.DISABLED)  #Button to stop tracking a new scenario
        self.stop_track_button.pack(side=tk.LEFT, padx=10)
        
        self.speed_forward_button = tk.Button(button_frame, text="Play Backwards", command=self.speed_forward)  #Button to toggle between backwards and forwards playback
        self.speed_forward_button.pack(side=tk.LEFT, padx = 10)

        self.end_button = tk.Button(button_frame, text = "Jump to End", command = self.jump_to_end) #Button to jump to the end and begin reverse playback
        self.end_button.pack(side = tk.LEFT, padx = 10)
        
        self.casevar = IntVar() #Variable used for radio button on usefulness
        
        self.good_button = tk.Radiobutton(button_frame, text="Useful Case",variable = self.casevar, value = 0, command = self.sel)  #Button to mark current scenario as useful (sets casevar to 0)
        self.good_button.pack(side = tk.LEFT, padx = 10)
        
        self.faulty_button = tk.Radiobutton(button_frame, text="Not Useful Case",variable = self.casevar, value = 1, command = self.sel) #Button to mark current scenario as not useful (sets casevar to 1)
        self.faulty_button.pack(side = tk.LEFT, padx = 10)
        
        self.speeds = ["Frame-by-Frame", "0.5X", "Normal","2X","4X"]    #List of speeds for playback
        self.speedvar = StringVar() #String denoting the speed
        self.speedvar.set("Normal") #default speed is normal
        self.speedmenu = OptionMenu( button_frame, self.speedvar, *self.speeds, command = self.setspeed)    #Drop down menu for selecting the speed
        self.speedmenu.pack(side = tk.LEFT, padx = 10)
        
        self.save_button = tk.Button(button_frame, text = "Final Save", command=self.save)  #Button to save all scenarios for a click-based scenario and move to the next
        self.save_button.pack(side = tk.LEFT, padx = 60)
	
        self.is_playing = False #Flag to track if the video is playing
        self.is_playing_forward = True  # Flag to track playback direction
        self.fps = 10.0 #Frames_Per_Second
        self.delay = 100  # Default delay between frames (adjust as needed, normally 10xfps)
        self.timer_id = None  # ID to keep track of the after() callback
        self.track_writer = 0   #Variable to keep track of whether the user is in the middle of tracking a scenario or not
        self.start_time = 0 #Current scenario's start time
        self.stop_time = 0  #Current scenario's stOP time
        self.folderpath = ""    # path to image folder
        self.final_time = "00:00"   #total time of the current video
        self.speedval = 1   #variable marking the speed of the video, default = 1
        self.scenarios = {} #dictionary of scenarios
        self.scenario_id = 1    #scenario id within current click-based scenario

        self.dataframe = pd.DataFrame(columns=["Scenario Number","Start Time", "Stop Time", "Quality"]) #Dataframe for compilation of scenarios
        self.finalscenarionum = 1   #scenario id wrt to all scenarios being made for the output
        
        self.super_scenario_num = super_sen_num #Scenario number of click-based scenario
        self.super_scenario_start_time = super_sen_start_time #Start time of click-based scenario
        self.super_scenario_end_time = super_sen_end_time #End time of click-based scenario
        self.input_folder_path = inputfolder    #Path of input folder for joystick clicks csv file
        self.super_scenario_save = 0    #flag trigerred by the final save button
        self.current_image = None   #image currently being displayed
        self.open_image_folder()#Call to open the image folder

    def writedftocsv(self): #Function to write the dataframe into a csv file
        # Write the existing DataFrame to a CSV file
        file_path = self.input_folder_path
        file_path = file_path.rsplit('_',1)[0]  #Get rid of end-time
        file_path = file_path.rsplit('_',1)[0]  #Get rid of start-time
        file_path = file_path.rsplit('_',1)[0]  #Get rid of click-based scenario number
        file_path = file_path + "_object_based_scenarios.csv"   #format output csv location and name
        self.dataframe.to_csv(file_path, index=False)#write output csv
            
    def read_next(self):#Function to move to next click-based scenario once save is pressed
        raw_file_path = self.input_folder_path  #Format path to obtain path to joystick_clicks csv
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        csv_file_path = raw_file_path + "/joystick_clicks_period_20.csv"
        with open(csv_file_path, 'r') as csv_file:  #open joystick_clicks_period_20.csv
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header
            current_row = None
            for row in csv_reader:  #iterate through rows
                if int(row[0]) <= int(self.super_scenario_num): #keep going until we reach the row for the next click-based scenario
                    continue
                else:
                    current_row = row
                    break
            
            if current_row is not None: #if we haven't reached the end of joystick_clicks_period_20.csv
                self.super_scenario_num = current_row[0]    #Take data from csv to locate image folder
                self.super_scenario_start_time = current_row[1]
                self.super_scenario_end_time = current_row[2]
                #format image folder path
                self.input_folder_path = raw_file_path + '_' + str(self.super_scenario_num) + '_' + str(self.super_scenario_start_time) + '_' + str(self.super_scenario_end_time)
                print(self.input_folder_path)
                self.open_image_folder()    #open images
            else:
                # Call function to write dataframe to output file when there's no next row available
                self.writedftocsv()

    def open_image_folder(self):    #function to open folder where images are present
        folder_path_orig = self.input_folder_path
        folder_path = folder_path_orig + '/combined'    #format folder location
        if folder_path_orig:    #if folder exists
            self.image_folder_path = folder_path
            self.image_files = sorted([f for f in os.listdir(self.image_folder_path) if f.endswith(('.jpg', '.png'))])#iterate through images in ascending order and store in array
            self.folderpath = folder_path_orig
            fin = (len(self.image_files)-1)/10  #time of final frame in seconds 
            fin_min = int(fin//60)
            fin_sec = int(fin%60)
            self.final_time = f"{fin_min:02}:{fin_sec:02}" #time of final frame in minutes: seconds

    def clear_video_display(self):  #Function to clear the video screen and attributes to get ready for next video playback
        self.stop_video()  # Call the stop_video method
        # Explicitly clear the video attributes and label:
        self.image_folder_path = ''
        self.timer_id = None  # ID to keep track of the after() callback
        self.track_writer = 0
        self.start_time = 0
        self.stop_time = 0
        self.folderpath = ""
        self.final_time = "00:00"
        self.speedval = 1
        self.scenarios = {}
        self.scenario_id = 1
        self.video_label.config(image=None)  # Clear the image in the video label
        #self.master.update_idletasks()  # Process all pending events to update the GUI immediately
        #self.master.after(100, gc.collect)  # Delay garbage collection to ensure GUI has updated
        self.track_text.delete(1.0, tk.END)  # Clear the text box

    
    def ask_confirmation(self): #Function to ask the user for confirmation on the start and stop times of the current object-based scenario
        confirmation = messagebox.askyesno("Confirmation", "Are you sure about this scenario's start and end times?")
        if confirmation:
            # If yes is pressed, close the message box
            self.scenario_id +=1
            pass
        else:
            # If no is pressed, delete the most recent addition to the dictionary
            if len(self.scenarios) > 0:
                del self.scenarios[len(self.scenarios)]
                self.update_box()  # Update the displayed scenarios
            pass

    def play_video(self):   #funaction that starts playing the video
        if not self.is_playing:
            self.is_playing = True  #check off flag
            #self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)   #configure the pause button
            self.play_frames()  # Start playing frames based on current direction

    def pause_resume_video(self):   #function to pause and resume the video
        if self.is_playing:
            self.is_playing = False
            self.pause_button.config(text="Resume")
            self.master.after_cancel(self.timer_id)  # Cancel frame update
        else:
            self.is_playing = True
            self.pause_button.config(text="Pause")
            if self.is_playing_forward:
                self.play_frames()  # Resume playing frames forward
            else:
                self.play_reverse_frames()  # Resume playing frames bac

    def play_frames(self):
        if self.is_playing and self.current_frame_index < len(self.image_files):
            image_path = os.path.join(self.image_folder_path, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (1800, 700))
                img = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=img)
                self.video_label.config(image=img)
                self.video_label.image = img

                current_time = self.current_frame_index / 10.0
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02}:{seconds:02}/" + self.final_time      
                self.time_label.config(text=time_str)

                self.current_frame_index += 1
                self.timer_id = self.master.after(self.delay, self.play_frames)  # Schedule next frame
            else:
                self.stop_video()
        else:
            self.stop_video()

    def update_box(self):
        self.track_text.delete(1.0, tk.END)  # Clear the text box
        for scenario_id, scenario_data in self.scenarios.items():
            start_time = scenario_data['Start_Time']
            stop_time = scenario_data['End Time']
            start_time_min = start_time//60
            start_time_sec = start_time%60
            stop_time_min = stop_time//60
            stop_time_sec = stop_time%60
            quality = scenario_data['Quality']
            text = f"Scenario {scenario_id}: Start Time: {start_time_min}:{start_time_sec}, Stop Time: {stop_time_min}:{stop_time_sec}, Quality: {'Useful' if quality == 0 else 'Not Useful'}\n"
            self.track_text.insert(tk.END, text)

    def play_reverse_frames(self):
        if self.is_playing and self.current_frame_index >= 0:
            image_path = os.path.join(self.image_folder_path, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (1800, 700))
                img = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=img)
                self.video_label.config(image=img)
                self.video_label.image = img

                current_time = self.current_frame_index / self.fps
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02}:{seconds:02}/" + self.final_time
                self.time_label.config(text=time_str)

                self.current_frame_index -= 1
                self.timer_id = self.master.after(self.delay, self.play_reverse_frames)  # Schedule next frame
            else:
                self.stop_video()
        else:
            self.stop_video()

    def stop_video(self):
        self.is_playing = False
        self.is_playing_forward = True
        #self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.current_frame_index = 0
        self.time_label.config(text="00:00")
        
    def start_track(self):
        if not self.is_playing:
            self.stop_track_button.config(state=tk.NORMAL)
            return
    
        self.start_time = self.current_frame_index / self.fps
        self.track_writer = 1
        self.stop_track_button.config(state=tk.NORMAL)
        self.update_box()
        start_time_min = self.start_time//60
        start_time_sec = self.start_time%60
        text = f"Scenario {self.scenario_id}: Start Time: {start_time_min}:{start_time_sec}, Quality: {'Useful' if self.casevar.get() == 0 else 'Not Useful'}\n"
        self.track_text.insert(tk.END, text)
        
    def stop_track(self):
        if self.track_writer == 1:
            self.stop_time = self.current_frame_index / self.fps
            self.scenarios[len(self.scenarios)+1] = { 'Start_Time': self.start_time, 'End Time': self.stop_time, 'Quality': self.casevar.get() }

            self.start_track_button.config(state=tk.NORMAL)
            self.stop_track_button.config(state=tk.DISABLED)
            self.update_box()
            self.pause_resume_video()
            self.ask_confirmation()
            self.pause_resume_video()

    def speed_forward(self):
        self.pause_resume_video()
        if not self.is_playing_forward:
            self.is_playing_forward = True  # Switch to forward playback
            self.current_frame_index -=2
            self.speed_forward_button.config(text="Play Backwards")
        else:
            self.is_playing_forward = False  # Switch back to backward playback
            self.speed_forward_button.config(text="Play Forwards")
            self.current_frame_index +=1
        self.pause_resume_video()
    
    def save(self):
        ftwo = self.folderpath
        last_underscore_index = ftwo.rfind('_')
        ftwo = ftwo[:last_underscore_index]
        last_underscore_index = self.folderpath.rfind('_')
        ftwo = ftwo[:last_underscore_index]

        savefile_path = ftwo + f"_{self.super_scenario_num}.csv"
        
        #with open(savefile_path, 'w', newline='') as csv_file:
            #csv_writer = csv.writer(csv_file)
            #csv_writer.writerow(["Start Time", "Stop Time", "Quality(0:Useful Case, 1:Not Useful Case)"])
        for scenario_id, scenario_data in self.scenarios.items():
            start_time = scenario_data['Start_Time']
            stop_time = scenario_data['End Time']
            quality = scenario_data['Quality']
            self.dataframe = self.dataframe.append({"Scenario Number":self.finalscenarionum,"Start Time": start_time+self.super_scenario_start_time, "Stop Time": stop_time+self.super_scenario_start_time, "Quality": quality}, ignore_index=True)
            self.finalscenarionum += 1
        messagebox.showinfo("Info", f"Scenarios for Super Scenario {self.super_scenario_num} saved successfully!")
        self.super_scenario_save = 1
        self.clear_video_display()
        self.read_next()
            
    def jump_to_end(self):
        #self.stop_video()
        self.current_frame_index = len(self.image_files) - 3
        if(self.is_playing_forward):
            self.speed_forward()
    def sel(self):
        self.casevar.get()
    def setspeed(self,*args):
        speedtitle = self.speedvar.get()
        if(speedtitle == "Normal"):
            self.speedval = 1
            self.delay = 100
        elif(speedtitle == "2X"):
            self.speedval = 2
            self.delay = 50
        elif(speedtitle == "4X"):
            self.speedval = 4
            self.delay = 25
        elif(speedtitle == "0.5X"):
            self.speedval = 0.5
            self.delay = 200
        elif(speedtitle == "Frame-by-Frame"):
            self.speedval = 0
            self.delay = 1000
    def start_video(self):
        self.stop_video()
        self.play_video()
        
def main():
    root = tk.Tk()
    folder_path_o = filedialog.askdirectory(title="Select Raw Data Folder")
    if folder_path_o:
        csv_file_path = os.path.join(folder_path_o, 'joystick_clicks_period_20.csv')
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)  # Skip header
                first_row = next(csv_reader)  # Read the first data row
                super_scenario_num = first_row[0]
                super_scenario_start_time = first_row[1]
                super_scenario_end_time = first_row[2]
                folder_path_fin = folder_path_o + '_' + str(super_scenario_num) + '_' + str(super_scenario_start_time) + '_' + str(super_scenario_end_time)
                video_player = VideoPlayer(root,folder_path_fin,super_scenario_num,super_scenario_start_time,super_scenario_end_time)

    root.mainloop()

if __name__ == "__main__":
    main()
