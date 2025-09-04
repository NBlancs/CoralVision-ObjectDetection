import cv2
import threading
import numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  
from ultralytics import YOLO
import datetime  
import os

class YOLOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Object Detection")
        
        self.video_source = 0
        self.is_recording = False
        self.out = None
        self.vid = None
        self.output_filename = None
        self.fps = 30.0  # default fallback

        # Resolve model path relative to this script so it works regardless of CWD
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "coralvision-bv2.pt")
        if not os.path.exists(model_path):
            messagebox.showerror(
                "Model file not found",
                f"Could not find YOLO weights at:\n{model_path}\n\n"
                "Make sure 'coralvision-bv2' is in the same folder as this script."
            )
            # Fail fast; __del__ will handle partial init safely
            raise FileNotFoundError(model_path)

        self.model = YOLO(model_path)
        
        self.canvas = tk.Canvas(root, width=640, height=480)
        self.canvas.pack()
        
        self.record_button = tk.Button(root, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack()

        # Recording indicator label
        self.rec_label = tk.Label(root, text="Recording: OFF", fg="gray")
        self.rec_label.pack(pady=(4, 8))

        # Start video capture
        # use mp4 vid for testing
        # self.video_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coral.mp4")

        # To use your camera instead of a video file, comment out the next line:
        # self.video_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2videotesting.mp4")
        # and uncomment the following line:
        # self.video_source = 0

        self.vid = cv2.VideoCapture(self.video_source)
        if not self.vid.isOpened():
            messagebox.showerror("Video Source Error", f"Could not open video source:\n{self.video_source}")
        else:
            # Try to read FPS from the source; fall back to 30 if unavailable
            src_fps = self.vid.get(cv2.CAP_PROP_FPS)
            if src_fps and src_fps > 0 and not np.isnan(src_fps):
                self.fps = float(src_fps)
            else:
                self.fps = 30.0
            self.update()
    
    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.config(text="Start Recording")
            if self.out:
                self.out.release()
                self.out = None
            messagebox.showinfo("Recording", f"Recording stopped.\nSaved to {self.output_filename or 'file'}")
            self.output_filename = None
            # Update indicator
            self.rec_label.config(text="Recording: OFF", fg="gray")
        else:
            self.is_recording = True
            self.record_button.config(text="Stop Recording")
            
            # Generate a unique filename using the current timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = f'output_{timestamp}.mp4'
            # Defer VideoWriter creation until we have the first frame to ensure correct size
            messagebox.showinfo("Recording", f"Recording started. Saving to {self.output_filename}.")
            # Update indicator immediately
            self.rec_label.config(text="Recording: ON", fg="red")
    
    def update(self):
        if self.vid is None or not self.vid.isOpened():
            # Try again later in case camera becomes available
            self.root.after(500, self.update)
            return

        ret, frame = self.vid.read()
        if ret:
            # Perform prediction
            results = self.model.predict(source=frame, conf=0.6, show_conf=False)
            annotated_frame = results[0].plot()  # Get the annotated frame

            # Lazy-create the VideoWriter on first frame after recording starts
            if self.is_recording and self.out is None:
                # Use mp4v codec for .mp4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                h, w = annotated_frame.shape[:2]
                self.out = cv2.VideoWriter(self.output_filename, fourcc, self.fps, (w, h))
                if not self.out or not self.out.isOpened():
                    # Fail gracefully if writer could not open
                    self.is_recording = False
                    self.record_button.config(text="Start Recording")
                    self.out = None
                    err_path = self.output_filename
                    self.output_filename = None
                    messagebox.showerror(
                        "Recording Error",
                        f"Could not open video writer for:\n{err_path}\n\n"
                        "Try installing an OpenCV build with FFMPEG support or a compatible MP4 codec."
                    )
                    # Revert indicator on failure
                    self.rec_label.config(text="Recording: OFF", fg="gray")

            # If recording, write the frame to the video file
            if self.is_recording and self.out is not None:
                self.out.write(annotated_frame)
            
            # Convert the frame to a format suitable for Tkinter
            self.photo = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            self.photo = Image.fromarray(self.photo)  # Use PIL's Image.fromarray
            self.photo = ImageTk.PhotoImage(self.photo)  # Convert to PhotoImage
            
            # Update the canvas with the new frame
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        # Call this function again after 10 ms
        self.root.after(10, self.update)

    def __del__(self):
        try:
            if getattr(self, 'vid', None) is not None and self.vid.isOpened():
                self.vid.release()
        except Exception:
            pass
        try:
            if getattr(self, 'out', None):
                self.out.release()
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOApp(root)
    root.mainloop()