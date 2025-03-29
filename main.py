import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import os

import SpeechToText

shared_text = {}
class PhotoViewer:
    def __init__(self, root, image_folder):
        self.root = root
        self.root.title("Photo Viewer")
        self.root.geometry("600x600")
        self.root.config(bg="#f0f0f0")

        self.image_folder = image_folder
        self.image_files = [f for f in os.listdir(image_folder) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
        self.current_image_index = 0
        self.is_copeing = False  # Flag to track the COPE state

        # Label to display the image
        self.image_label = tk.Label(self.root, bg="#f0f0f0")
        self.image_label.pack(pady=20)

        # Frame for buttons
        self.button_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.button_frame.pack(pady=10)

        # Buttons for previous, next, and COPE
        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.prev_image, width=15, height=2,
                                     font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat")
        self.prev_button.grid(row=0, column=0, padx=10)

        self.cope_button = tk.Button(self.button_frame, text="Start COPE-ing", command=self.toggle_cope, width=15,
                                     height=2, font=("Arial", 12, "bold"), bg="#2ecc71", fg="white", relief="flat")
        self.cope_button.grid(row=0, column=1, padx=10)

        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_image, width=15, height=2,
                                     font=("Arial", 12, "bold"), bg="#e74c3c", fg="white", relief="flat")
        self.next_button.grid(row=0, column=2, padx=10)

        self.show_image()

    def show_image(self):
        # Load and display the current image
        image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])
        image = Image.open(image_path)
        image = ImageTk.PhotoImage(image.resize((500, 500)))  # Resize to fit window

        self.image_label.config(image=image)
        self.image_label.image = image  # Keep a reference to avoid garbage collection

    def prev_image(self):
        # Go to the previous image
        self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
        self.show_image()

    def next_image(self):
        # Go to the next image
        self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        self.show_image()

    def toggle_cope(self):
        # Toggle the COPE button between "Start COPE-ing" and "Stop COPE-ing"
        if self.is_copeing:

            self.cope_button.config(text="Start COPE-ing", bg="#2ecc71")
            obj_of_speaker = SpeechToText.SpeechToText(shared_text)
            obj_of_speaker.run()
            # Change back to Start COPE-ing
            self.is_copeing = False
        else:
            self.cope_button.config(text="Stop COPE-ing", bg="#e67e22")  # Change to Stop COPE-ing
            self.is_copeing = True


root = tk.Tk()

# Create an instance of PhotoViewer
image_folder = "/home/blux/PycharmProjects/for_hackathon/generated_images"  # Replace with the path to your image folder
viewer = PhotoViewer(root, image_folder)

# Start the Tkinter main loop
root.mainloop()
