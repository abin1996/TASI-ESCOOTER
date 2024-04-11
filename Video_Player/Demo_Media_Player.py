import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, master):
        self.master = master
        self.master.title("Python Video Player")
        self.master.geometry("800x600")

        self.video_path = None
        self.cap = None
        self.video_label = tk.Label(self.master)
        self.video_label.pack()

        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        open_button = tk.Button(button_frame, text="Open Video", command=self.open_video)
        open_button.pack(side=tk.LEFT, padx=10)

        self.play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        self.play_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(button_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=10)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_video)
        stop_button.pack(side=tk.LEFT, padx=10)

        rewind_button = tk.Button(button_frame, text="Rewind", command=self.rewind_video)
        rewind_button.pack(side=tk.LEFT, padx=10)

        fast_forward_button = tk.Button(button_frame, text="Fast Forward", command=self.fast_forward_video)
        fast_forward_button.pack(side=tk.LEFT, padx=10)

        self.is_playing = False
        self.delay = 30  # milliseconds

    def open_video(self):
        file_path = filedialog.askopenfilename(title="Select a Video File", filetypes=[("Video Files", "*.mp4;*.avi;*.mkv")])
        if file_path:
            self.video_path = file_path

    def play_video(self):
        if self.video_path and not self.is_playing:
            self.cap = cv2.VideoCapture(self.video_path)
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

    def show_frame(self):
        if self.cap is not None and self.cap.isOpened() and self.is_playing:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (800, 600))
                img = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=img)
                self.video_label.config(image=img)
                self.video_label.image = img
                self.master.after(self.delay, self.show_frame)
            else:
                self.stop_video()

    def stop_video(self):
        if self.cap is not None:
            self.cap.release()
            self.video_label.config(image=None)
            self.is_playing = False
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def rewind_video(self):
        if self.cap is not None and self.cap.isOpened():
            current_pos = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            new_pos = max(0, current_pos - 2000)  # Rewind by 2 seconds
            self.cap.set(cv2.CAP_PROP_POS_MSEC, new_pos)
            if not self.is_playing:
                self.show_frame()

    def fast_forward_video(self):
        if self.cap is not None and self.cap.isOpened():
            current_pos = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            total_duration = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS) * 1000
            new_pos = min(total_duration, current_pos + 2000)  # Fast forward by 2 seconds
            self.cap.set(cv2.CAP_PROP_POS_MSEC, new_pos)
            if not self.is_playing:
                self.show_frame()

def main():
    root = tk.Tk()
    video_player = VideoPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
