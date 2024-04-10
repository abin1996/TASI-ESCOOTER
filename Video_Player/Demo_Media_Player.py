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

        play_button = tk.Button(button_frame, text="Play", command=self.play_video)
        play_button.pack(side=tk.LEFT, padx=10)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_video)
        stop_button.pack(side=tk.LEFT, padx=10)

    def open_video(self):
        file_path = filedialog.askopenfilename(title="Select a Video File", filetypes=[("Video Files", "*.mp4;*.avi;*.mkv")])
        if file_path:
            self.video_path = file_path

    def play_video(self):
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            self.show_frame()

    def show_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (800, 600))  # Resize frame to fit the window
                img = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=img)
                self.video_label.config(image=img)
                self.video_label.image = img  # Keep reference to avoid garbage collection
                self.master.after(30, self.show_frame)  # Update frame every 30 milliseconds
            else:
                self.stop_video()

    def stop_video(self):
        if self.cap is not None:
            self.cap.release()
            self.video_label.config(image=None)

def main():
    root = tk.Tk()
    video_player = VideoPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
