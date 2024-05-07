import tkinter as tk
from tkinter import filedialog, messagebox, IntVar, W, CENTER, StringVar, OptionMenu
import cv2
from PIL import Image, ImageTk
import os
import csv

class VideoPlayer:
    def __init__(self, master):
        self.master = master
        self.master.title("Image to Video Player")
        self.master.geometry("800x700")

        self.image_folder_path = None
        self.image_files = []
        self.current_frame_index = 0
        self.video_label = tk.Label(self.master)
        self.video_label.pack()

        self.time_label = tk.Label(self.master, text="00:00")
        self.time_label.pack(pady=10)

        self.track_text = tk.Text(self.master, height=5, width=60)
        self.track_text.pack(pady=10)

        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        open_button = tk.Button(button_frame, text="Open Folder", command=self.open_image_folder)
        open_button.pack(side=tk.LEFT, padx=10)

        self.start_button = tk.Button(button_frame, text = "Jump to Start", command = self.start_video)
        self.start_button.pack(side=tk.LEFT, padx=10)
        #self.play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        #self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=10)

        #stop_button = tk.Button(button_frame, text="Restart", command=self.stop_video)
        #stop_button.pack(side=tk.LEFT, padx=10)

        self.start_track_button = tk.Button(button_frame, text="Set Start Time", command=self.start_track)
        self.start_track_button.pack(side=tk.LEFT, padx=10)

        self.stop_track_button = tk.Button(button_frame, text="Set Stop Time", command=self.stop_track, state=tk.DISABLED)
        self.stop_track_button.pack(side=tk.LEFT, padx=10)
        
        self.speed_forward_button = tk.Button(button_frame, text="Play Backwards", command=self.speed_forward)
        self.speed_forward_button.pack(side=tk.LEFT, padx = 10)

        self.end_button = tk.Button(button_frame, text = "Jump to End", command = self.jump_to_end)
        self.end_button.pack(side = tk.LEFT, padx = 10)
        
        self.casevar = IntVar()
        
        self.good_button = tk.Radiobutton(button_frame, text="Good Case",variable = self.casevar, value = 0, command = self.sel)
        self.good_button.pack(side = tk.LEFT, padx = 10)
        
        self.faulty_button = tk.Radiobutton(button_frame, text="Bad Case",variable = self.casevar, value = 1, command = self.sel)
        self.faulty_button.pack(side = tk.LEFT, padx = 10)
        
        self.speeds = ["Frame-by-Frame", "0.5X", "Normal","2X","4X"]
        self.speedvar = StringVar()
        self.speedvar.set("Normal")
        self.speedmenu = OptionMenu( button_frame, self.speedvar, *self.speeds, command = self.setspeed)
        self.speedmenu.pack(side = tk.LEFT, padx = 10)
        
        self.save_button = tk.Button(button_frame, text = "Save", command=self.save)
        self.save_button.pack(side = tk.LEFT, padx = 60)
	
        self.is_playing = False
        self.is_playing_forward = True  # Flag to track playback direction
        self.delay = 100  # Default delay between frames (adjust as needed)
        self.timer_id = None  # ID to keep track of the after() callback
        self.track_file = None
        self.track_writer = None
        self.start_time = 0
        self.folderpath = ""
        self.final_time = "00:00"
        self.speedval = 1

    def open_track_times(self):
        #csv_file_path = filedialog.askopenfilename(title="Open Track Times CSV", filetypes=[("CSV Files", "*.csv")])
        csv_file_path = "track_times.csv"
        if csv_file_path:
            try:
                with open(csv_file_path, 'r') as csv_file:
                    reader = csv.reader(csv_file)
                    track_times = list(reader)

                if track_times:
                    self.track_text.delete(1.0, tk.END)  # Clear previous contents
                    iter = 1
                    for start, stop in track_times:
                        if iter == 1:
                            iter+=1
                            continue
                        else:
                            self.track_text.insert(tk.END, f"Start: {start}, Stop: {stop}\n")
                else:
                    messagebox.showinfo("Track Times", "No track times recorded.")

            except Exception as e:
                messagebox.showerror("Error", f"Error opening CSV file: {str(e)}")

    def open_image_folder(self):
        folder_path_orig = filedialog.askdirectory(title="Select a Folder with Images")
        folder_path = folder_path_orig + '/combined'
        if folder_path_orig:
            self.image_folder_path = folder_path
            self.image_files = sorted([f for f in os.listdir(self.image_folder_path) if f.endswith(('.jpg', '.png'))])
            self.folderpath = folder_path_orig
            fin = (len(self.image_files)-1)/10
            fin_min = int(fin//60)
            fin_sec = int(fin%60)
            self.final_time = f"{fin_min:02}:{fin_sec:02}"

    def play_video(self):
        if not self.is_playing:
            self.is_playing = True
            #self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.play_frames()  # Start playing frames based on current direction

    def pause_resume_video(self):
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

                current_time = self.current_frame_index / 10.0
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
    
        if self.track_writer is None:
            # Start tracking
            self.start_time = self.current_frame_index / 10.0
            self.track_file = open('track_times.csv', 'a', newline='')
            self.track_writer = csv.writer(self.track_file)
            self.stop_track_button.config(state=tk.NORMAL)
        else:
            # Overwrite start_time if tracking is already started
            self.start_time = self.current_frame_index / 10.0
            self.stop_track_button.config(state=tk.NORMAL)
            self.open_track_times()
        self.track_text.insert(tk.END, f"Start: {self.start_time}\n")

    def stop_track(self):
        if self.track_writer is not None:
            stop_time = self.current_frame_index / 10.0
            csv_file_path = 'track_times.csv'

        # Open CSV file in write mode to clear existing data
            with open(csv_file_path, 'w', newline='') as csv_file:
                self.track_writer = csv.writer(csv_file)
                self.track_writer.writerow(["Start Time", "Stop Time"])

        # Write new track times
            with open(csv_file_path, 'a', newline='') as csv_file:
                self.track_writer = csv.writer(csv_file)
                self.track_writer.writerow([self.start_time, stop_time])

            self.start_track_button.config(state=tk.NORMAL)
            self.stop_track_button.config(state=tk.DISABLED)
        self.open_track_times()

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
        savefile_path = self.folderpath + ".csv"
        with open('track_times.csv', 'r') as csv_file:
            reader = csv.reader(csv_file)
            track_times = list(reader)
            for row in track_times:
                row.append(self.casevar.get())
        
        # Adding header
        track_times = track_times[1:]
        track_times.insert(0, ["Start Time", "Stop Time", "Quality(0:Good Case, 1:Bad Case)"])

        with open(savefile_path, 'w', newline='') as csv_file:
            self.track_writer = csv.writer(csv_file)
            self.track_writer.writerows(track_times)

        if os.path.exists("track_times.csv"):
            os.remove("track_times.csv")
        
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
    video_player = VideoPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
