import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time

class VideoPlayerApp:
    def __init__(self, video_sources):
        self.root = tk.Tk()
        self.root.title("Video Player")

        self.num_videos = len(video_sources)
        self.video_captures = [cv2.VideoCapture(src) for src in video_sources]

        self.width = int(self.video_captures[0].get(cv2.CAP_PROP_FRAME_WIDTH) / 4)
        self.height = int(self.video_captures[0].get(cv2.CAP_PROP_FRAME_HEIGHT) / 4.5)

        self.canvases = []
        self.canvas_images = []
        self.paused = False  # Single pause state for all videos

        for i in range(self.num_videos):
            canvas = tk.Canvas(self.root, width=self.width, height=self.height)
            canvas.grid(row=i // 3, column=i % 3)
            self.canvases.append(canvas)

            # Create placeholder image on canvas
            empty_image = Image.new("RGB", (self.width, self.height))
            photo = ImageTk.PhotoImage(empty_image)
            image_item = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas_images.append((canvas, photo, image_item))

        # Add single pause/resume button
        self.pause_button = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_button.grid(row=self.num_videos // 3 + 1, column=1, columnspan=self.num_videos % 3 or 3)

        self.threads = []
        for idx in range(self.num_videos):
            thread = threading.Thread(target=self.update, args=(idx,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def update(self, idx):
        try:
            desired_fps = 10
            while True:
                if not self.paused:
                    start_time = time.time()

                    ret, frame = self.video_captures[idx].read()
                    if not ret:
                        break

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rgb_frame = cv2.resize(rgb_frame, (self.width, self.height))

                    photo = ImageTk.PhotoImage(Image.fromarray(rgb_frame))

                    # Update canvas image with new photo
                    self.canvases[idx].itemconfig(self.canvas_images[idx][2], image=photo)
                    self.canvas_images[idx] = (self.canvases[idx], photo, self.canvas_images[idx][2])

                    self.root.update_idletasks()

                    # Calculate time to sleep for desired FPS
                    elapsed_time = time.time() - start_time
                    sleep_time = max(0, 1.0/desired_fps - elapsed_time)
                    time.sleep(sleep_time)

        except Exception as e:
            print(f"Error in update thread {idx}: {e}")

        self.video_captures[idx].release()

    def toggle_pause(self):
        self.paused = not self.paused
        btn_text = "Resume" if self.paused else "Pause"
        self.pause_button.config(text=btn_text)

    def on_close(self):
        for cap in self.video_captures:
            if cap.isOpened():
                cap.release()
        self.root.quit()

if __name__ == "__main__":
    video_paths = [
        "images1_2022-08-06-11-40-29_0_camera1_image_color_compressed.mp4",
        "images2_2022-08-06-11-40-29_0_camera2_image_color_compressed.mp4",
        "images3_2022-08-06-11-40-29_0_camera3_image_color_compressed.mp4",
        "images4_2022-08-06-11-40-29_0_camera4_image_color_compressed.mp4",
        "images5_2022-08-06-11-40-29_0_camera5_image_color_compressed.mp4",
        "images6_2022-08-06-11-40-29_0_camera6_image_color_compressed.mp4"
    ]
    app = VideoPlayerApp(video_paths)
