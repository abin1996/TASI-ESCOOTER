import tkinter as tk    #IMPORTS
from tkinter import filedialog, messagebox, IntVar, W, CENTER, StringVar, OptionMenu
import cv2
from PIL import Image, ImageTk
import os
import csv
import gc
import pandas as pd
import sys
class VideoPlayer:
    def __init__(self, master, csv_file, image_path_fin, image_path, super_scenario_num, super_scenario_start_time, super_scenario_end_time, super_scenario_escooter,super_scenario_bike,last_super_scenario_num, raw_data_name, ob_scenario_save_path, data_frame):
        self.master = master #tkinter root
        self.master.title("Image to Video Player")
        self.master.geometry("800x700") #Size of Window. Adjusted for PC Screen, Change if code is used on a different screen
        
        self.csv_file = csv_file #Path of the joystick clicks file
        self.image_path_fin = image_path_fin #Path to frames for current CB-Scenario
        self.image_path = image_path #Path to folder containing CB-Scenario image folders
        self.super_scenario_num = super_scenario_num #Current CB-Scenario number
        self.super_scenario_start_time = super_scenario_start_time #Current CB-Scenario Start Time
        self.super_scenario_end_time = super_scenario_end_time #Current CB-Scenario End Time
        self.raw_data_name = raw_data_name #Raw_Data_Folder Name
        self.last_super_scenario_num = last_super_scenario_num  #Number of CB-Scenarios
        
        self.image_files = []   #List of image files
        self.current_frame_index = 0    #index keeping track of current frame
        self.video_label = tk.Label(self.master)    #initialize video with tkinter
        self.video_label.pack() #pack() is a method of arranging things on the screen, in this case the video
        
        self.time_label = tk.Label(self.master, text="00:00")   #Initialize a Time Label keeping track of the time from the beginning of the video
        self.time_label.pack(pady=2)
        
        self.folder_label = tk.Label(self.master, text=f"Raw Data Folder: {self.raw_data_name} \n Click-Based Scenario Number: {self.super_scenario_num}/{self.last_super_scenario_num}")
        self.folder_label.pack(pady=2)
        
        self.escooter_presence = tk.Label(self.master, text = f"")#Indicator indicating the presence of escooters
        self.escooter_presence.pack(pady = 2)
        self.bike_presence = tk.Label(self.master,text = f"")#Indicator indicating the presence of bikes
        self.bike_presence.pack(pady = 2)
        if(int(super_scenario_escooter) == 0):#Are there escooters?
            self.super_scenario_escooter = 0
        else:
            self.super_scenario_escooter = 1
        if(int(super_scenario_bike) == 0):#Are there bikes?      
            self.super_scenario_bike = 0
        else:
            self.super_scenario_bike = 1
        if(self.super_scenario_bike == 1):
            self.bike_presence.config(text = f"This CB-Scenario contains sightings of bikes")#Tell the user what to expect
        if(self.super_scenario_escooter == 1):
            self.escooter_presence.config(text = f"This CB-Scenario contains sightings of escooters")
        
        self.track_text = tk.Text(self.master, height=5, width=81)  #Text box where users can see current and previous tracking information
        self.track_text.pack(pady=2)

        button_frame = tk.Frame(self.master)    #Frame for all buttons
        button_frame.pack(pady=2)

        self.start_button = tk.Button(button_frame, text = "Jump to Start", command = self.start_video) #Button to play the video from the start
        self.start_button.pack(side=tk.LEFT, padx=5)   #Start/Restart CB-Scenario playback
        
        self.end_button = tk.Button(button_frame, text = "Jump to End", command = self.jump_to_end) #Button to jump to the end and begin reverse playback
        self.end_button.pack(side = tk.LEFT, padx = 5)
        
        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)   #Button to pause or resume the video playback
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.speed_forward_button = tk.Button(button_frame, text="Play Backwards", command=self.speed_forward)  #Button to toggle between backwards and forwards playback
        self.speed_forward_button.pack(side=tk.LEFT, padx = 5)
        
        self.speeds = ["Frame-by-Frame", "0.5X", "Normal","2X","4X"]    #List of speeds for playback
        self.speedvar = StringVar() #String denoting the speed
        self.speedvar.set("Normal") #default speed is normal
        self.speedmenu = OptionMenu( button_frame, self.speedvar, *self.speeds, command = self.setspeed)    #Drop down menu for selecting the speed
        self.speedmenu.pack(side = tk.LEFT, padx = 5)

        self.start_track_button = tk.Button(button_frame, text="Set Start Time", command=self.start_track)  #Button to start tracking a new scenario
        self.start_track_button.pack(side=tk.LEFT, padx=5)

        self.stop_track_button = tk.Button(button_frame, text="Set Stop Time", command=self.stop_track, state=tk.DISABLED)  #Button to stop tracking a new scenario
        self.stop_track_button.pack(side=tk.LEFT, padx=5)
                
        self.casevar = IntVar() #Variable used for radio button on usefulness
        
        self.good_button = tk.Radiobutton(button_frame, text="Useful Case",variable = self.casevar, value = 0, command = self.sel)  #Button to mark current scenario as useful (sets casevar to 0)
        self.good_button.pack(side = tk.LEFT, padx = 5)
        
        self.faulty_button = tk.Radiobutton(button_frame, text="Not Useful Case",variable = self.casevar, value = 1, command = self.sel) #Button to mark current scenario as not useful (sets casevar to 1)
        self.faulty_button.pack(side = tk.LEFT, padx = 5)
        
        self.save_button = tk.Button(button_frame, text = "Save and Move to Next CB-Scenario", command=self.save, bg = "#90EE90")  #Button to save all scenarios for a click-based scenario and move to the next
        self.save_button.pack(side = tk.LEFT, padx = 30)

        self.reset_button = tk.Button(button_frame, text = "Reset Scenarios", command = self.reset, bg = "#FFCCCC")
        self.reset_button.pack(side = tk.LEFT, padx = 20)
	
        self.is_playing = False #Flag to track if the video is playing
        self.is_playing_forward = True  # Flag to track playback direction
        self.fps = 10.0 #Frames_Per_Second
        self.delay = 100  # Default delay between frames (adjust as needed, normally 10xfps)
        self.timer_id = None  # ID to keep track of the after() callback
        self.track_writer = 0   #Variable to keep track of whether the user is in the middle of tracking a scenario or not
        self.start_time = 0 #Current scenario's start time
        self.stop_time = 0  #Current scenario's stOP time
        self.final_time = "00:00"   #total time of the current video
        self.speedval = 1   #variable marking the speed of the video, default = 1
        self.scenarios = {} #dictionary of scenarios
        self.scenario_id = 1    #scenario id within current click-based scenario

        self.dataframe = data_frame #Dataframe for compilation of scenarios
        if self.dataframe.empty:
            self.finalscenarionum = 1   #scenario id wrt to all scenarios being made for the output
        else:
            self.finalscenarionum = self.dataframe.index[-1]
        
        self.super_scenario_save = 0    #flag trigerred by the final save button
        self.current_image = None   #image currently being displayed
        self.ob_scenario_path = ob_scenario_save_path
        self.open_image_folder()#Call to open the image folder
    
    def writedftocsv(self): #Function to write the dataframe into a csv file
        # Write the existing DataFrame to a CSV file
        file_path = os.path.join(self.ob_scenario_path,self.raw_data_name)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_path = os.path.join(file_path,"object_based_scenarios.csv")
        self.dataframe.to_csv(file_path, index=False)#write output csv
            
    def read_next(self):#Function to move to next click-based scenario once save is pressed
        csv_file_path = self.csv_file
        with open(csv_file_path, 'r') as csv_file:  #open joystick_clicks_period_20.csv
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header
            current_row = None
            for row in csv_reader:  #iterate through rows
                #if(int(row[0]) > 2):##Code to test for n super scenarios
                #   break
                if int(row[0]) <= int(self.super_scenario_num): #keep going until we reach the row for the next click-based scenario
                    continue
                else:
                    current_row = row
                    break
            
            if current_row is not None: #if we haven't reached the end of joystick_clicks_period_20.csv
                self.super_scenario_num = current_row[0]    #Take data from csv to locate image folder
                self.super_scenario_start_time = current_row[1]
                self.super_scenario_end_time = current_row[2]
                super_scenario_escooter = current_row[5]
                super_scenario_bike = current_row[6]
                if(int(super_scenario_escooter) == 0):        
                    self.super_scenario_escooter = 0
                else:
                    self.super_scenario_escooter = 1
                if(int(super_scenario_bike) == 0):        
                    self.super_scenario_bike = 0
                else:
                    self.super_scenario_bike = 1
                if(self.super_scenario_bike == 1):
                    self.bike_presence.config(text = f"This CB-Scenario contains sightings of bikes")
                if(self.super_scenario_escooter == 1):
                    self.escooter_presence.config(text = f"This CB-Scenario contains sightings of escooters")
                #format image folder path
                fpath = self.raw_data_name + '_' + str(self.super_scenario_num) + '_' + str(self.super_scenario_start_time) + '_' + str(self.super_scenario_end_time)
                self.image_path_fin = os.path.join(self.image_path,fpath)
                self.folder_label.config(text=f"Raw Data Folder: {self.raw_data_name} \n Click-Based Scenario Number: {str(self.super_scenario_num)}/{str(self.last_super_scenario_num)}")
                ob_csv_path = os.path.join(self.ob_scenario_path, self.raw_data_name, "object_based_scenarios.csv")
                self.dataframe = pd.read_csv(ob_csv_path)
                self.open_image_folder()    #open images
            else:
                # Call function to write dataframe to output file when there's no next row available
                self.writedftocsv()
                sys.exit("Completed All CB scenarios for this Folder")
    def open_image_folder(self):
        image_folder_path = self.image_path_fin
        combined_folder_path = os.path.join(image_folder_path, 'combined')
        if os.path.exists(combined_folder_path):
            self.image_path_fin = combined_folder_path
            self.image_files = sorted([f for f in os.listdir(self.image_path_fin) if f.endswith(('.jpg', '.png'))])
            fin = (len(self.image_files)-1)/self.fps
            fin_min = int(fin//60)
            fin_sec = int(fin%60)
            self.final_time = f"{fin_min:02}:{fin_sec:02}"

    def clear_video_display(self):  #Function to clear the video screen and attributes to get ready for next video playback
        self.stop_video()  # Call the stop_video method
        # Explicitly clear the video attributes and label:
        self.image_path_fin = ''
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

    def play_video(self):   #function that starts playing the video
        if not self.is_playing:
            self.is_playing = True  #check off flag
            #self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)   #configure the pause button
            self.play_frames()  # Start playing frames based on current direction

    def pause_resume_video(self):   #function to pause and resume the video
        if self.is_playing:
            self.is_playing = False #toggle flag
            self.pause_button.config(text="Resume") #toggle pause/resume text
            self.master.after_cancel(self.timer_id)  # Cancel frame update
        else:
            self.is_playing = True #toggle flag
            self.pause_button.config(text="Pause") #toggle pause/resume text
            if self.is_playing_forward:
                self.play_frames()  # Resume playing frames forward
            else:
                self.play_reverse_frames()  # Resume playing frames backwards

    def play_frames(self):  #Main function to play frames in the forward direction
        if self.is_playing and self.current_frame_index < len(self.image_files):
            image_path = os.path.join(self.image_path_fin, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)  #configure image path for each image
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  #set image colors
                screen_width = self.master.winfo_screenwidth()
                screen_height = self.master.winfo_screenheight()
                image_width = int(screen_width * 0.8)  # Adjust as needed
                image_height = int(screen_height * 0.6)  # Adjust as needed
                frame = cv2.resize(frame, (image_width, image_height))  #set image size as width, height. Adjust as necessary. Note: If forward image size is changed, backward image size also needs to be changed
                img = Image.fromarray(frame)#obtain image from image array
                img = ImageTk.PhotoImage(image=img)#play images
                self.video_label.config(image=img)
                self.video_label.image = img

                current_time = self.current_frame_index / self.fps  #update current time since start of video play
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02}:{seconds:02}/" + self.final_time      #print current time since video play against total video time
                self.time_label.config(text=time_str)

                self.current_frame_index += 1
                self.timer_id = self.master.after(self.delay, self.play_frames)  # Schedule next frame
            else:
                self.stop_video()
        else:
            self.stop_video()

    def update_box(self):#function to update the text box that shows users scenario tracking info
        self.track_text.delete(1.0, tk.END)  # Clear the text box
        for scenario_id, scenario_data in self.scenarios.items():
            start_time = scenario_data['Start_Time']
            stop_time = scenario_data['End Time']
            start_time_min = int (start_time//60) #calculate scenario start time in minutes and seconds for display
            start_time_sec = int (start_time%60)
            stop_time_min = int (stop_time//60) #calculate scenario end time in minutes and seconds for display
            stop_time_sec = int (stop_time%60)
            quality = scenario_data['Quality'] #Quality of scenario
            #Display start time, end time and quality of scenario tracked
            text = f"Object Based Scenario {scenario_id}: Start Time: {start_time_min}:{start_time_sec}, Stop Time: {stop_time_min}:{stop_time_sec}, Quality: {'Useful' if quality == 0 else 'Not Useful'}\n"
            self.track_text.insert(tk.END, text)

    def play_reverse_frames(self): #Main function to play frames in the reverse direction
        if self.is_playing and self.current_frame_index >= 0:
            image_path = os.path.join(self.image_path_fin, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)  #configure image path for each image
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #set image colors
                screen_width = self.master.winfo_screenwidth()
                screen_height = self.master.winfo_screenheight()
                image_width = int(screen_width * 0.8)  # Adjust as needed
                image_height = int(screen_height * 0.6)  # Adjust as needed
                frame = cv2.resize(frame, (image_width, image_height)) #set image size as width, height. Adjust as necessary. Note: If forward image size is changed, backward image size also needs to be changed
                img = Image.fromarray(frame) #obtain image from image array
                img = ImageTk.PhotoImage(image=img) #play images
                self.video_label.config(image=img)
                self.video_label.image = img

                current_time = self.current_frame_index / self.fps #update current time since start of video play
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02}:{seconds:02}/" + self.final_time  #print current time since video play against total video time
                self.time_label.config(text=time_str)

                self.current_frame_index -= 1
                self.timer_id = self.master.after(self.delay, self.play_reverse_frames)  # Schedule next frame
            else:
                self.stop_video()
        else:
            self.stop_video()

    def stop_video(self):   #Function that stops video playback and resets video to start
        self.is_playing = False #trigger flags
        self.is_playing_forward = True
        #self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED) #disable pause when video stops
        self.current_frame_index = 0    #reset frame index
        self.time_label.config(text="00:00")#reset time
        
    def start_track(self):
        self.stop_track_button.config(state=tk.NORMAL)
        self.start_time = self.current_frame_index / self.fps   #calculate start time of new scenario
        self.track_writer = 1   #update variable flag for tracking
        self.stop_track_button.config(state=tk.NORMAL)  #enable stop track button
        self.update_box()   #update text box with latest tracking info.
        start_time_min = int(self.start_time // 60)
        start_time_sec = int(self.start_time % 60)
        #Display scenario start time in Min:Sec for user
        text = f"Object Based Scenario {self.scenario_id}: Start Time: {start_time_min}:{start_time_sec}, Quality: {'Useful' if self.casevar.get() == 0 else 'Not Useful'}\n"
        self.track_text.insert(tk.END, text)

        
    def stop_track(self): #Function to stopt tracking a scenario
        if self.track_writer == 1:
            stop_time = self.current_frame_index / self.fps #Calculate scenario stop time
            self.pause_resume_video()#pause video
            confirmation = messagebox.askyesno("Confirmation", f"Are you sure about the OB-Scenario Stop Time: {stop_time}?")
            if(confirmation):
                self.stop_time = stop_time
                self.scenarios[len(self.scenarios)+1] = { 'Start_Time': self.start_time, 'End Time': self.stop_time, 'Quality': self.casevar.get() }#update scenario attributes to dictionary
                self.start_track_button.config(state=tk.NORMAL)#configure buttons
                self.stop_track_button.config(state=tk.DISABLED)
                self.update_box()#update box with tracking information
                self.ask_confirmation()#ask for confirmation on current scenario start and end time
                self.pause_resume_video()#resume video
                self.track_writer = 0
            else:
                self.pause_resume_video()

    def speed_forward(self):    #function to toggle forward and backward video playback
        self.pause_resume_video()   #pause video
        if not self.is_playing_forward:
            self.is_playing_forward = True  # Switch to forward playback
            self.current_frame_index -=2
            self.speed_forward_button.config(text="Play Backwards")
        else:
            self.is_playing_forward = False  # Switch back to backward playback
            self.speed_forward_button.config(text="Play Forwards")
            self.current_frame_index +=1
        self.pause_resume_video()   #resume video
    
    def save(self): #button to save all scenarios tracked for current click-based scenario
        #ftwo = self.folderpath  #Configure output path for csv
        #last_underscore_index = ftwo.rfind('_')
        #ftwo = ftwo[:last_underscore_index]
        #last_underscore_index = self.folderpath.rfind('_')
        #ftwo = ftwo[:last_underscore_index]

        #savefile_path = ftwo + f"_{self.super_scenario_num}.csv"
        
        #with open(savefile_path, 'w', newline='') as csv_file:
            #csv_writer = csv.writer(csv_file)
            #csv_writer.writerow(["Start Time", "Stop Time", "Quality(0:Useful Case, 1:Not Useful Case)"])
        confirmation = messagebox.askyesno("Confirmation", f"Are you sure you are done with Click Based Scenario {self.super_scenario_num}?")
        if confirmation:
            self.bike_presence.config(text = f"")
            self.escooter_presence.config(text = f"")
            for scenario_id, scenario_data in self.scenarios.items(): #for each new scenario
                start_time = scenario_data['Start_Time']
                stop_time = scenario_data['End Time']
                quality = scenario_data['Quality']
            #append the scenario to the dataframe
                self.dataframe = pd.concat([ self.dataframe, pd.DataFrame({ "Scenario Number": [self.finalscenarionum], "Start Time": [float(start_time) + float(self.super_scenario_start_time)],"Stop Time": [float(stop_time) + float(self.super_scenario_start_time)],"Quality": [quality], "CB-Scenario Number": [self.super_scenario_num]})], ignore_index=True)
                self.finalscenarionum += 1#increment the total number of scenarios for the final output
            self.writedftocsv()            
            messagebox.showinfo("Info", f"Object-Based Scenarios for Click-Based Scenario {self.super_scenario_num} saved successfully!")
            self.super_scenario_save = 1#check save flag
            self.clear_video_display()#clear current video from display
            self.read_next()#load next video

    def reset(self):
        confirm = messagebox.askyesno("Confirmation", f"Are you sure you want to reset all object based scenarios for Click Based Scenario {self.super_scenario_num}?")
        if confirm:
            self.track_text.delete(1.0, tk.END)
            self.scenarios.clear()
            self.timer_id = None  # ID to keep track of the after() callback
            self.track_writer = 0
            self.start_time = 0
            self.stop_time = 0
            self.scenario_id = 1
                
    def jump_to_end(self):#function to jump to the end of the video and play backward
        #self.stop_video()
        self.current_frame_index = len(self.image_files) - 3    #Grant a difference of two frames to account for processing time
        if(self.is_playing_forward):
            self.speed_forward()

    def sel(self):  #function to update quality attribute
        self.casevar.get()

    def setspeed(self,*args):   #function called by dropdown menu to set speed of video playback:
        speedtitle = self.speedvar.get()
        if(speedtitle == "Normal"):#1X
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
    
    def start_video(self):  #Function to play video from the start
        self.stop_video()
        self.play_video()
def find_last_super_scenario_num(csv_file):
    last_super_scenario_num = None
    if isinstance(csv_file, str):
        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                last_super_scenario_num = row[0]
    else:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            last_super_scenario_num = row[0]
    return last_super_scenario_num

def main():
    root = tk.Tk() #Initialize TKinter
    image_path = filedialog.askdirectory(title = "Select Image Folder")#Select folder with cb-scenario image folders
    grandpa_path = os.path.dirname(os.path.dirname(image_path))
    raw_data_name = os.path.split(image_path)[1]
    if image_path:
        csv_folder = os.path.join(grandpa_path, "click_based_scenarios_joy_csv", raw_data_name)#Select the folder with the Joystick_Clicks_csv file
        if csv_folder:
            csv_file = os.path.join(csv_folder,"joystick_clicks_period_20.csv")
            ob_scenario_save_path = os.path.join(grandpa_path, "Object_Based_Scenario_Metadata")
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as csv_file_o:  #open csv
                    csv_reader = csv.reader(csv_file_o)
                    next(csv_reader)  # Skip header
                    first_row = next(csv_reader)  # Read the first data row
                    super_scenario_num = first_row[0]   #CB-Scenario Number
                    super_scenario_start_time = first_row[1]    #CB-Scenario Start-Time
                    super_scenario_end_time = first_row[2]  #CB-Scenario End-Time
                    super_scenario_escooter = first_row[5]  #CB-Scenario E-Scooters
                    super_scenario_bike = first_row[6]  #CB-Scenario Bikes
                    raw_data_name = os.path.split(image_path)[1] #Find the name of the folder from the path
                    cb_scenario_image_folder = raw_data_name + '_' + str(super_scenario_num) + '_' + str(super_scenario_start_time) + '_' + str(super_scenario_end_time)
                    image_path_fin = os.path.join(image_path, cb_scenario_image_folder)
                    last_super_scenario_num = find_last_super_scenario_num(csv_file)
                    existing_op_file = os.path.join(ob_scenario_save_path,raw_data_name,"object_based_scenarios.csv")
                    if os.path.exists(existing_op_file):
                        df = pd.read_csv(existing_op_file)
                        last_row = df.iloc[-1]
                        scen_done_upto = int(last_row[4])
                        if(scen_done_upto == last_super_scenario_num):
                            response = messagebox.askyesno("Confirm", "This raw data folder has already been completed. Working on it again will cause it to be overwritten. Proceed?")
                            if response:
                                df = pd.DataFrame()
                            else:
                                return
                        else:
                            while(int(super_scenario_num) <= scen_done_upto):
                                first_row = next(csv_reader)  # Read the first data row
                                super_scenario_num = first_row[0]   #CB-Scenario Number
                                super_scenario_start_time = first_row[1]    #CB-Scenario Start-Time
                                super_scenario_end_time = first_row[2]  #CB-Scenario End-Time
                                super_scenario_escooter = first_row[5]  #CB-Scenario E-Scooters
                                super_scenario_bike = first_row[6]  #CB-Scenario Bikes
                                raw_data_name = os.path.split(image_path)[1] #Find the name of the folder from the path
                                cb_scenario_image_folder = raw_data_name + '_' + str(super_scenario_num) + '_' + str(super_scenario_start_time) + '_' + str(super_scenario_end_time)
                                image_path_fin = os.path.join(image_path, cb_scenario_image_folder)
                            decision = messagebox.askyesno("Notification", f"CB-Scenarios 1-{int(super_scenario_num)-1} completed. Would you like to continue with the next scenario (Yes) or Exit the Application (No)?")
                            if not decision:
                                return
                    else:
                        df = pd.DataFrame(columns=["Scenario Number","Start Time", "Stop Time", "Quality","CB-Scenario Number"]) #Dataframe for compilation of scenarios
                    video_player = VideoPlayer(root, csv_file, image_path_fin, image_path, super_scenario_num, super_scenario_start_time, super_scenario_end_time, super_scenario_escooter,super_scenario_bike,last_super_scenario_num, raw_data_name,ob_scenario_save_path, df)#Create an Instance of the Video-Player Class
    root.mainloop()#Keep Tkinter running until the User quits
if __name__ == "__main__":
    main()