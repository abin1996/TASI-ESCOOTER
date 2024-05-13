import tkinter as tk    #IMPORTS
from tkinter import filedialog, messagebox, IntVar, W, CENTER, StringVar, OptionMenu
import cv2
from PIL import Image, ImageTk
import os
import csv
import gc
import pandas as pd
class VideoPlayer:
    def __init__(self, master, inputfolder, super_sen_num, super_sen_start_time, super_sen_end_time, folder_path_o):   #Initialize VideoPlayer
        self.master = master
        self.master.title("Image to Video Player")
        self.master.geometry("800x700") #Size of Window. Adjusted for0 PC Screen, Change if code is used on a different screen

        
        self.image_folder_path = None   #Path to the frames/images for playback
        self.image_files = []   #List of image files
        self.current_frame_index = 0    #index keeping track of current frame
        self.video_label = tk.Label(self.master)    #initialize video with tkinter
        self.video_label.pack() #pack() is a method of arranging things on the screen, in this case the video

        self.time_label = tk.Label(self.master, text="00:00")   #Initialize a Time Label keeping track of the time from the beginning of the video
        self.time_label.pack(pady=10)
        self.csvpath = folder_path_o
                
        self.inputfolder = inputfolder
        self.rawdatafolder = inputfolder.rsplit("_",1)[0]
        self.rawdatafolder = self.rawdatafolder.rsplit("_",1)[0]
        self.rawdatafolder = self.rawdatafolder.rsplit("_",1)[0]
        rawdata = os.path.split(self.rawdatafolder)[1]
        self.folder_label = tk.Label(self.master, text=f"Raw Data Folder: {rawdata} \n Click-Based Scenario Number: {super_sen_num}")
        self.folder_label.pack(pady=10)

        self.track_text = tk.Text(self.master, height=5, width=81)  #Text box where users can see current and previous tracking information
        self.track_text.pack(pady=10)

        button_frame = tk.Frame(self.master)    #Frame for all buttons
        button_frame.pack(pady=10)

        #open_button = tk.Button(button_frame, text="Open Folder", command=self.scenario_iterator)
        #open_button.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(button_frame, text = "Jump to Start", command = self.start_video) #Button to play the video from the start
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.end_button = tk.Button(button_frame, text = "Jump to End", command = self.jump_to_end) #Button to jump to the end and begin reverse playback
        self.end_button.pack(side = tk.LEFT, padx = 10)
        #self.play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        #self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)   #Button to pause or resume the video playback
        self.pause_button.pack(side=tk.LEFT, padx=10)

        #stop_button = tk.Button(button_frame, text="Restart", command=self.stop_video)
        #stop_button.pack(side=tk.LEFT, padx=10)

        self.speed_forward_button = tk.Button(button_frame, text="Play Backwards", command=self.speed_forward)  #Button to toggle between backwards and forwards playback
        self.speed_forward_button.pack(side=tk.LEFT, padx = 10)
        
        self.speeds = ["Frame-by-Frame", "0.5X", "Normal","2X","4X"]    #List of speeds for playback
        self.speedvar = StringVar() #String denoting the speed
        self.speedvar.set("Normal") #default speed is normal
        self.speedmenu = OptionMenu( button_frame, self.speedvar, *self.speeds, command = self.setspeed)    #Drop down menu for selecting the speed
        self.speedmenu.pack(side = tk.LEFT, padx = 10)

        self.start_track_button = tk.Button(button_frame, text="Set Start Time", command=self.start_track)  #Button to start tracking a new scenario
        self.start_track_button.pack(side=tk.LEFT, padx=10)

        self.stop_track_button = tk.Button(button_frame, text="Set Stop Time", command=self.stop_track, state=tk.DISABLED)  #Button to stop tracking a new scenario
        self.stop_track_button.pack(side=tk.LEFT, padx=10)
                
        self.casevar = IntVar() #Variable used for radio button on usefulness
        
        self.good_button = tk.Radiobutton(button_frame, text="Useful Case",variable = self.casevar, value = 0, command = self.sel)  #Button to mark current scenario as useful (sets casevar to 0)
        self.good_button.pack(side = tk.LEFT, padx = 10)
        
        self.faulty_button = tk.Radiobutton(button_frame, text="Not Useful Case",variable = self.casevar, value = 1, command = self.sel) #Button to mark current scenario as not useful (sets casevar to 1)
        self.faulty_button.pack(side = tk.LEFT, padx = 10)
        
        self.save_button = tk.Button(button_frame, text = "Save and Move to Next CB-Scenario", command=self.save, bg = "#90EE90")  #Button to save all scenarios for a click-based scenario and move to the next
        self.save_button.pack(side = tk.LEFT, padx = 60)

        self.reset_button = tk.Button(button_frame, text = "Reset Scenarios", command = self.reset, bg = "#FFCCCC")
        self.reset_button.pack(side = tk.LEFT, padx = 40)
	
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
        #file_path = os.path.join(self.csvpath,self.rawdatafolder,self.rawdatafolder + "_object_based_scenarios.csv")   #format output csv location and name
        file_path = os.path.join(self.rawdatafolder,"object_based_scenarios.csv")
        #print(self.csvpath)
        #print(self.rawdatafolder)
        #print(file_path)
        #file_path = file_path.rsplit('_',1)[0]  #Get rid of end-time
        #file_path = file_path.rsplit('_',1)[0]  #Get rid of start-time
        #file_path = file_path.rsplit('_',1)[0]  #Get rid of click-based scenario number
        self.dataframe.to_csv(file_path, index=False)#write output csv
            
    def read_next(self):#Function to move to next click-based scenario once save is pressed
        raw_file_path = self.input_folder_path  #Format path to obtain path to joystick_clicks csv
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        raw_file_path = raw_file_path.rsplit('_',1)[0]
        csv_file_path = os.path.join(raw_file_path , "joystick_clicks_period_20.csv")
        with open(csv_file_path, 'r') as csv_file:  #open joystick_clicks_period_20.csv
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header
            current_row = None
            for row in csv_reader:  #iterate through rows
                if(int(row[0]) > 2):##Code tot est for n super scenarios
                   break
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
                raw_folder_path = os.path.split(raw_file_path)[1]
                self.folder_label.config(text=f"Raw Data Folder: {raw_folder_path} \n Click-Based Scenario Number: {str(self.super_scenario_num)}")
                self.open_image_folder()    #open images
            else:
                # Call function to write dataframe to output file when there's no next row available
                self.writedftocsv()

    def open_image_folder(self):
        # Move up two directories from the input folder
        parent_folder = os.path.abspath(os.path.join(self.inputfolder, os.pardir))
        grandparent_folder = os.path.abspath(os.path.join(parent_folder, os.pardir))
        # Enter Extracted_Click_Based_Scenarios
        image_folder_path = os.path.join(grandparent_folder, "Extracted_Click_Based_Scenarios", self.rawdatafolder)
        combined_folder_path = os.path.join(image_folder_path, 'combined')
        
        if os.path.exists(combined_folder_path):
            self.image_folder_path = combined_folder_path
            self.image_files = sorted([f for f in os.listdir(self.image_folder_path) if f.endswith(('.jpg', '.png'))])
            self.folderpath = image_folder_path
            fin = (len(self.image_files)-1)/10
            fin_min = int(fin//60)
            fin_sec = int(fin%60)
            self.final_time = f"{fin_min:02}:{fin_sec:02}"

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
            image_path = os.path.join(self.image_folder_path, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)  #configure image path for each image
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  #set image colors
                frame = cv2.resize(frame, (1575, 750))  #set image size as width, height. Adjust as necessary. Note: If forward image size is changed, backward image size also needs to be changed
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
            image_path = os.path.join(self.image_folder_path, self.image_files[self.current_frame_index])
            frame = cv2.imread(image_path)  #configure image path for each image
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #set image colors
                frame = cv2.resize(frame, (1575, 750)) #set image size as width, height. Adjust as necessary. Note: If forward image size is changed, backward image size also needs to be changed
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
        
    def start_track(self):  #Function to start tracking a scenario
        if not self.is_playing:
            self.stop_track_button.config(state=tk.NORMAL)
            return
    
        self.start_time = self.current_frame_index / self.fps   #calculate start time of new scenario
        self.track_writer = 1   #update variable flag for tracking
        self.stop_track_button.config(state=tk.NORMAL)  #enable stop track button
        self.update_box()   #update text box with latest tracking info.
        start_time_min = int(self.start_time//60)
        start_time_sec = int(self.start_time%60)
        #Display scenario start time in Min:Sec for user
        text = f"Object Based Scenario {self.scenario_id}: Start Time: {start_time_min}:{start_time_sec}, Quality: {'Useful' if self.casevar.get() == 0 else 'Not Useful'}\n"
        self.track_text.insert(tk.END, text)
        
    def stop_track(self): #Function to stopt tracking a scenario
        if self.track_writer == 1:
            self.stop_time = self.current_frame_index / self.fps #Calculate scenario stop time
            self.scenarios[len(self.scenarios)+1] = { 'Start_Time': self.start_time, 'End Time': self.stop_time, 'Quality': self.casevar.get() }#update scenario attributes to dictionary
            self.start_track_button.config(state=tk.NORMAL)#configure buttons
            self.stop_track_button.config(state=tk.DISABLED)
            self.update_box()#update box with tracking information
            self.pause_resume_video()#pause video
            self.ask_confirmation()#ask for cnfirmation on current scenario start and end time
            self.pause_resume_video()#resume video
            self.track_writer = 0

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
            for scenario_id, scenario_data in self.scenarios.items(): #for each new scenario
                start_time = scenario_data['Start_Time']
                stop_time = scenario_data['End Time']
                quality = scenario_data['Quality']
            #append the scenario to the dataframe
                self.dataframe = pd.concat([ self.dataframe, pd.DataFrame({ "Scenario Number": [self.finalscenarionum], "Start Time": [float(start_time) + float(self.super_scenario_start_time)],"Stop Time": [float(stop_time) + float(self.super_scenario_start_time)],"Quality": [quality]})], ignore_index=True)
                self.finalscenarionum += 1#increment the total number of scenarios for the final output
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
        
def main():
    root = tk.Tk()#initialize tkinter
    folder_path_o = filedialog.askdirectory(title="Select Raw Data Folder") #select folder with joystick_clicks_period_20.csv
    if folder_path_o:
        csv_file_path = os.path.join(folder_path_o, 'joystick_clicks_period_20.csv')
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r') as csv_file:  #open csv
                csv_reader = csv.reader(csv_file)
                next(csv_reader)  # Skip header
                first_row = next(csv_reader)  # Read the first data row
                super_scenario_num = first_row[0]
                super_scenario_start_time = first_row[1]
                super_scenario_end_time = first_row[2]
                folder_path_fin = folder_path_o + '_' + str(super_scenario_num) + '_' + str(super_scenario_start_time) + '_' + str(super_scenario_end_time) #configure folder path for video playback
                video_player = VideoPlayer(root,folder_path_fin,super_scenario_num,super_scenario_start_time,super_scenario_end_time, folder_path_o) #instance of the videoplayer class

    root.mainloop()#keep tkinter running until user quits

if __name__ == "__main__":
    main()
