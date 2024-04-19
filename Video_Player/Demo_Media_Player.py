import tkinter as tk
from tkinter import filedialog, messagebox
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

        self.play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=10)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_video)
        stop_button.pack(side=tk.LEFT, padx=10)

        rewind_button = tk.Button(button_frame, text="Rewind (2s)", command=self.rewind_video)
        rewind_button.pack(side=tk.LEFT, padx=10)

        fast_forward_button = tk.Button(button_frame, text="Fast Forward (2s)", command=self.fast_forward_video)
        fast_forward_button.pack(side=tk.LEFT, padx=10)

        self.start_track_button = tk.Button(button_frame, text="Set Start Time", command=self.start_track)
        self.start_track_button.pack(side=tk.LEFT, padx=10)

        self.stop_track_button = tk.Button(button_frame, text="Set Stop Time", command=self.stop_track, state=tk.DISABLED)
        self.stop_track_button.pack(side=tk.LEFT, padx=10)
        
        self.open_csv_button = tk.Button(button_frame, text="Open Track Times", command=self.open_track_times)
        self.open_csv_button.pack(side=tk.LEFT, padx=10)

        self.is_playing = False
        self.delay = 16
        self.track_file = None
        self.track_writer = None
        self.start_time = 0

    def open_track_times(self):
        csv_file_path = filedialog.askopenfilename(title="Open Track Times CSV", filetypes=[("CSV Files", "*.csv")])
        if csv_file_path:
            try:
                with open(csv_file_path, 'r') as csv_file:
                    reader = csv.reader(csv_file)
                    track_times = list(reader)

                if track_times:
                    self.track_text.delete(1.0, tk.END)  # Clear previous contents
                    for start, stop in track_times:
                        self.track_text.insert(tk.END, f"Start: {start}, Stop: {stop}\n")

                else:
                    messagebox.showinfo("Track Times", "No track times recorded.")

            except Exception as e:
                messagebox.showerror("Error", f"Error opening CSV file: {str(e)}")

    def open_image_folder(self):
        folder_path = filedialog.askdirectory(title="Select a Folder with Images")
        if folder_path:
            self.image_folder_path = folder_path
            self.image_files = sorted([f for f in os.listdir(self.image_folder_path) if f.endswith(('.jpg', '.png'))])

    def play_video(self):
        if self.image_files and not self.is_playing:
            self.is_playing = True
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.show_frame()

    def pause_resume_video(self):
        if self.is_playing:
            self.is_playing = False
            self.pause_button.config(text="Resume")
        else:
            self.is_playing = True
            self.pause_button.config(text="Pause")
            self.show_frame()

    def stop_video(self):
        self.is_playing = False
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.current_frame_index = 0
        self.time_label.config(text="00:00")

    def rewind_video(self):
        if self.is_playing:
            self.current_frame_index = max(0, self.current_frame_index - 120)
            self.show_frame()

    def fast_forward_video(self):
        if self.is_playing:
            self.current_frame_index = min(len(self.image_files) - 1, self.current_frame_index + 120)
            self.show_frame()
    def show_frame(self):
        if self.is_playing:
            if self.current_frame_index < len(self.image_files):
                image_path = os.path.join(self.image_folder_path, self.image_files[self.current_frame_index])
                frame = cv2.imread(image_path)
                if frame is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (800, 600))
                    img = Image.fromarray(frame)
                    img = ImageTk.PhotoImage(image=img)
                    self.video_label.config(image=img)
                    self.video_label.image = img

                    current_time = self.current_frame_index / 60.0
                    minutes = int(current_time // 60)
                    seconds = int(current_time % 60)
                    time_str = f"{minutes:02}:{seconds:02}"
                    self.time_label.config(text=time_str)

                    self.current_frame_index += 1
                    self.master.after(self.delay, self.show_frame)
                else:
                    self.stop_video()
            else:
                self.stop_video()
                
    def start_track(self):
        if not self.is_playing:
            self.stop_track_button.config(state=tk.NORMAL)
            return
    
        if self.track_writer is None:
            # Start tracking
            self.start_time = self.current_frame_index / 60.0
            self.track_file = open('track_times.csv', 'a', newline='')
            self.track_writer = csv.writer(self.track_file)
            self.stop_track_button.config(state=tk.NORMAL)
        else:
            # Overwrite start_time if tracking is already started
            self.start_time = self.current_frame_index / 60.0
            self.stop_track_button.config(state=tk.NORMAL)

    def stop_track(self):
        if self.track_writer is not None:
            stop_time = self.current_frame_index / 60.0
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

    
def main():
    root = tk.Tk()
    video_player = VideoPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
