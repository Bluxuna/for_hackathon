




#                     -------- -----------------------------------------------         COPE           ----------------------------------------------



'''ძაან ცუდი პრაქტიკაა ვიცი როცა ყველაფერს ერთ ფაილში წერ უბრალოდ სხვა რამის მოსაფიქრებლად დრო არ მეყო ბოდიშIთ !!!
დაბილდვის გამო მოგვიხდა რომ ის ობიექტები რაც ცალკე ფაილებში გვაქ აქ გაგვეერთიანებია
'''

import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from tkinter.font import Font
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk
import os
import datetime
import time
import uuid
import requests
import speech_recognition as sr
import threading
import queue
import typing
from deep_translator import GoogleTranslator

# Create necessary directories
script_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs("generated_images", exist_ok=True)
os.makedirs("new_generated", exist_ok=True)


class Translator:
    def __init__(self, source='auto', target='en'):
        self.source = source
        self.target = target

    def translate(self, text: typing.Union[str, typing.List[str]]):
        return GoogleTranslator(source=self.source, target=self.target).translate(text)


class ImageGenerator:
    """
    Generates images from prompts using Pollinations AI, with error handling and cropping.
    """

    def __init__(self, save_path="new_generated"):
        """
        Initializes the ImageGenerator with a save path.
        """
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)
        self.stop_generation = False

    def _generate_unique_prompt(self, prompt):
        """
        Appends a UUID to the prompt to ensure uniqueness.
        """
        return f"{prompt}{uuid.uuid4()}".replace(" ", "-")

    def _download_and_save_image(self, url, image_save_path):
        """
        Downloads an image from a URL and saves it to a file.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            with open(image_save_path, 'wb') as f:
                f.write(response.content)

            return True

        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            return False

    def _crop_image(self, image_save_path):
        """
        Crops the image to remove watermarks or artifacts.
        """
        try:
            image = Image.open(image_save_path)
            cropped_image = image.crop((0, 0, image.width, image.height - 100))
            cropped_image.save(image_save_path)
            return True

        except Exception as e:
            print(f"Image cropping failed: {e}")
            return False

    def generate_image(self, prompt):
        """
        Generates an image from a prompt, downloads it, crops it, and returns the path.
        """
        if not prompt or self.stop_generation:
            return None

        formatted_prompt = self._generate_unique_prompt(prompt)
        url = f"https://image.pollinations.ai/prompt/{formatted_prompt}"

        timestamp = int(time.time())
        image_save_name = f"gen_img_{timestamp}.png"
        image_save_path = os.path.join(self.save_path, image_save_name)

        if self._download_and_save_image(url, image_save_path):
            if self._crop_image(image_save_path):
                return image_save_path

        return None


class SpeechToText:
    def __init__(self, shared_data, callback=None):
        """
        Initializes the transcriber with a queue and recognizer.
        """
        self.text_queue = queue.Queue()
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.shared_data = shared_data
        self.running = True
        self.callback = callback
        self.transcription_thread = None
        self.printing_thread = None

    def transcribe_audio(self):
        """
        Continuously transcribes Georgian audio and puts results in the queue.
        """
        try:
            with sr.Microphone() as microphone:
                self.recognizer.adjust_for_ambient_noise(microphone)
                while self.running:
                    try:
                        audio = self.recognizer.listen(microphone, timeout=5)
                        text = self.recognizer.recognize_google(audio, language="ka-GE")
                        self.text_queue.put(text.lower())
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        self.text_queue.put(f"Google Speech Recognition error: {e}")
                    except TimeoutError:
                        pass  # do nothing if timeout, just continue.
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")

        except Exception as e:
            print(f"Microphone error: {e}")

    def print_transcriptions(self):
        """
        Continuously processes transcriptions from the queue.
        """
        while self.running:
            try:
                text = self.text_queue.get(timeout=1)
                if text and not text.startswith("Google Speech Recognition error:"):
                    translated_text = self.translator.translate(text)
                    self.shared_data["text"] = translated_text

                    # Log transcriptions
                    with open("outputKA.txt", "a+", encoding="utf-8") as file:
                        file.write('\n' + str(text))
                    with open("outputEN.txt", "a+", encoding="utf-8") as file:
                        file.write('\n' + str(translated_text))

                    print(f"Original: {text}")
                    print(f"Translated: {translated_text}")

                    # Call the callback function with the translated text
                    if self.callback:
                        self.callback(translated_text)

            except queue.Empty:
                pass  # do nothing if empty

    def start(self):
        """
        Starts the transcription and printing threads.
        """
        self.running = True
        self.transcription_thread = threading.Thread(target=self.transcribe_audio)
        self.printing_thread = threading.Thread(target=self.print_transcriptions)

        self.transcription_thread.daemon = True
        self.printing_thread.daemon = True

        self.transcription_thread.start()
        self.printing_thread.start()

    def stop(self):
        """
        Stops the transcription and printing threads.
        """
        self.running = False
        if self.transcription_thread and self.printing_thread:
            if self.transcription_thread.is_alive():
                self.transcription_thread.join(timeout=2)
            if self.printing_thread.is_alive():
                self.printing_thread.join(timeout=2)


class PhotoViewer:
    def __init__(self, root, image_folder, parent_window=None):
        self.parent_window = parent_window

        # Create a new Toplevel window if not provided
        if root is None:
            self.root = tk.Toplevel()
        else:
            self.root = root

        self.root.title("Photo Viewer")
        self.root.geometry("600x600")
        self.root.config(bg="#f0f0f0")

        self.image_folder = image_folder
        self.image_files = [f for f in os.listdir(image_folder) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
        self.current_image_index = 0
        self.is_coping = False  # Flag to track the COPE state

        # Create shared data dictionary
        self.shared_data = {}

        # Create image generator
        self.image_generator = ImageGenerator(save_path="new_generated")

        # Create speech recognition object
        self.speech_to_text = SpeechToText(self.shared_data, callback=self.on_speech_recognized)

        # Store the original image path to return to later
        self.original_image_path = None
        self.current_displayed_image_path = None

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

        # Status label
        self.status_label = tk.Label(self.root, text="Ready", bg="#f0f0f0", font=("Arial", 10))
        self.status_label.pack(pady=5)

        # Button to return to main app
        if self.parent_window:
            back_button = tk.Button(self.root, text="Back to Main Menu", command=self.go_back_to_main,
                                    font=("Arial", 11), bg="#6c757d", fg="white", relief="flat", padx=10, pady=5)
            back_button.pack(pady=10)

        if self.image_files:
            self.show_image()

    def go_back_to_main(self):
        # Stop any ongoing processes
        if self.is_coping:
            self.toggle_cope()  # Turn off COPE mode

        # Destroy this window and show parent
        self.root.destroy()
        if self.parent_window:
            self.parent_window.deiconify()

    def show_image(self, image_path=None):
        if not image_path and self.image_files:
            # Load and display the current image from the folder
            image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])

        if image_path and os.path.exists(image_path):
            self.current_displayed_image_path = image_path

            try:
                image = Image.open(image_path)
                # Calculate new dimensions while maintaining aspect ratio
                width, height = image.size
                max_size = 500

                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)

                image = ImageTk.PhotoImage(image.resize((new_width, new_height)))

                self.image_label.config(image=image)
                self.image_label.image = image  # Keep a reference to avoid garbage collection
            except Exception as e:
                print(f"Error displaying image: {e}")
        else:
            # Clear the image if no path provided or file doesn't exist
            self.image_label.config(image=None)
            self.image_label.image = None

    def prev_image(self):
        if not self.is_coping and self.image_files:
            # Go to the previous image
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.show_image()

    def next_image(self):
        if not self.is_coping and self.image_files:
            # Go to the next image
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.show_image()

    def on_speech_recognized(self, text):
        """Callback when speech is recognized and translated"""
        if self.is_coping and text:
            self.status_label.config(text=f"Generating image for: {text}")
            self.root.update()

            # Generate image in a separate thread to avoid blocking the UI
            threading.Thread(target=self.generate_and_display_image, args=(text,), daemon=True).start()

    def generate_and_display_image(self, prompt):
        """Generate an image and display it"""
        if self.is_coping:
            image_path = self.image_generator.generate_image(prompt)
            if image_path:
                # Update UI from the main thread
                self.root.after(0, lambda: self.show_image(image_path))
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Image generated: {os.path.basename(image_path)}"))

    def toggle_cope(self):
        # Toggle the COPE button between "Start COPE-ing" and "Stop COPE-ing"
        if self.is_coping:
            # Stop COPE-ing
            self.cope_button.config(text="Start COPE-ing", bg="#2ecc71")
            self.status_label.config(text="Stopped COPE-ing")

            # Stop speech recognition
            self.speech_to_text.stop()

            # Stop image generation
            self.image_generator.stop_generation = True

            # Return to original gallery image
            if self.original_image_path:
                self.show_image(self.original_image_path)
                self.original_image_path = None

            # Re-enable navigation buttons
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)

            self.is_coping = False
        else:
            # Start COPE-ing
            self.cope_button.config(text="Stop COPE-ing", bg="#e67e22")
            self.status_label.config(text="Listening for speech...")

            # Store the current image path
            self.original_image_path = self.current_displayed_image_path

            # Enable image generation
            self.image_generator.stop_generation = False

            # Start speech recognition
            self.speech_to_text.start()

            # Disable navigation buttons while coping
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

            self.is_coping = True


def create_stylish_tkinter_window():
    window = tk.Tk()
    window.title("SPEECH-TO-VISUALIZATION")
    window.geometry("650x300")
    window.configure(bg="#f8f9fa")  # Light background color

    primary_color = "#4361ee"  # main name,submit btn, the line
    secondary_color = "#3a0ca3"  # submit shadow
    accent_color = "#4361ee"  # Light blue
    text_color = "#2b2d42"  # font color
    bg_color = "#f8f9fa"  # Light gray background

    title_font = Font(family="Helvetica", size=14, weight="bold")
    label_font = Font(family="Helvetica", size=11)
    button_font = Font(family="Helvetica", size=10, weight="bold")

    style = ttk.Style()
    style.theme_use('clam')

    style.configure("TLabel", background=bg_color, foreground=text_color, font=label_font)
    style.configure("Title.TLabel", font=title_font, foreground=primary_color, background=bg_color)

    style.configure("Primary.TButton",
                    font=button_font,
                    background=primary_color,
                    foreground="white",
                    padding=8)
    style.map("Primary.TButton",
              background=[("active", secondary_color), ("pressed", secondary_color)],
              foreground=[("active", "white"), ("pressed", "white")])

    style.configure("Secondary.TButton",
                    font=button_font,
                    background="#e9ecef",
                    foreground=text_color,
                    padding=8)
    style.map("Secondary.TButton",
              background=[("active", "#dee2e6"), ("pressed", "#ced4da")],
              foreground=[("active", text_color), ("pressed", text_color)])

    style.configure("Accent.TButton",
                    font=button_font,
                    background=accent_color,
                    foreground="white",
                    padding=8)
    style.map("Accent.TButton",
              background=[("active", "#90e0ef"), ("pressed", "#90e0ef")],
              foreground=[("active", "white"), ("pressed", "white")])

    style.configure("TEntry", padding=8, font=label_font)
    style.configure("TFrame", background=bg_color)

    header_frame = tk.Frame(window, bg=primary_color, height=5)
    header_frame.pack(fill=tk.X)

    separator = ttk.Separator(window, orient='horizontal')
    separator.pack(fill=tk.X, pady=2)

    title_label = ttk.Label(window, text="Speech-to-Visualization", style="Title.TLabel")
    title_label.pack(pady=15)

    main_frame = ttk.Frame(window, padding="20 10 20 10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # -------------Start Topic section-----------------
    topic_frame = ttk.Frame(main_frame, padding="0 5 0 5")
    topic_frame.pack(fill=tk.X, pady=5)

    topic_label = ttk.Label(topic_frame, text="Enter Topic Name:")
    topic_label.pack(side=tk.LEFT, padx=5)

    entry = ttk.Entry(topic_frame)
    entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    topic_display = ttk.Label(main_frame, text="", font=button_font)
    topic_display.pack(pady=5)

    def get_entry_text():
        entry_text = entry.get()
        if entry_text:
            topic_display.config(text=f"Topic: {entry_text}")
            flash_success_message(topic_display)
        else:
            messagebox.showwarning("Warning", "Please enter a topic name.")

    def flash_success_message(widget):
        original_bg = widget.cget("background")
        widget.configure(background="#4ade80")
        widget.update_idletasks()
        window.after(800, lambda: widget.configure(background=original_bg))

    submit_button = ttk.Button(topic_frame, text="SUBMIT", command=get_entry_text, style="Primary.TButton")
    submit_button.pack(side=tk.LEFT, padx=5)

    separator2 = ttk.Separator(main_frame, orient='horizontal')
    separator2.pack(fill=tk.X, pady=10)

    # -----------Start Actions section-------------------
    actions_frame = ttk.Frame(main_frame, padding="0 5 0 5")
    actions_frame.pack(fill=tk.X)

    actions_label = ttk.Label(actions_frame, text="Actions:", font=button_font)
    actions_label.pack(side=tk.LEFT, padx=5)

    def open_photo_viewer():
        # Hide the main window
        window.withdraw()

        # Open the PhotoViewer
        image_folder = "./generated_images"  # Replace with the path to your image folder
        viewer = PhotoViewer(None, image_folder, parent_window=window)

    record_btn = ttk.Button(
        actions_frame,
        text="Start Recording",
        command=open_photo_viewer,  # Use the function from lastHope.py
        style="Accent.TButton"
    )
    record_btn.pack(side=tk.LEFT, padx=5)

    slideshow_btn = ttk.Button(
        actions_frame,
        text="Generate Slideshow",
        command=lambda: open_slideshow_manager(window, primary_color, secondary_color, accent_color, bg_color,
                                               title_font, label_font, button_font),
        style="Secondary.TButton"
    )
    slideshow_btn.pack(side=tk.LEFT, padx=5)

    status_frame = tk.Frame(window, bg="#e9ecef", height=25)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    status_label = tk.Label(status_frame, text="Ready", bg="#e9ecef", fg="#6c757d", anchor=tk.W, padx=10)
    status_label.pack(fill=tk.X, side=tk.LEFT)

    window.mainloop()


def open_slideshow_manager(parent, primary_color, secondary_color, accent_color, bg_color, title_font, label_font,
                           button_font):
    slideshow_window = tk.Toplevel(parent)
    slideshow_window.title("Slideshow Manager")
    slideshow_window.geometry("550x550")
    slideshow_window.configure(bg=bg_color)

    header_frame = tk.Frame(slideshow_window, bg=secondary_color, height=5)
    header_frame.pack(fill=tk.X)

    title_label = tk.Label(
        slideshow_window,
        text="Manage Slideshow Subjects",
        font=title_font,
        bg=bg_color,
        fg=primary_color
    )
    title_label.pack(pady=15)

    main_container = tk.Frame(slideshow_window, bg=bg_color, padx=20, pady=10)
    main_container.pack(fill=tk.BOTH, expand=True)

    input_frame = tk.Frame(main_container, bg=bg_color)
    input_frame.pack(fill=tk.X, pady=10)

    subject_label = tk.Label(input_frame, text="Subject Name:", bg=bg_color, font=label_font)
    subject_label.pack(side=tk.LEFT, padx=5)

    subject_entry = tk.Entry(
        input_frame,
        width=30,
        font=label_font,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground="#ced4da",
        highlightcolor=primary_color
    )
    subject_entry.pack(side=tk.LEFT, padx=5)

    list_frame = tk.Frame(main_container, bg=bg_color, pady=10)
    list_frame.pack(fill=tk.BOTH, expand=True)

    list_label = tk.Label(list_frame, text="Added Subjects:", bg=bg_color, font=label_font, anchor=tk.W)
    list_label.pack(fill=tk.X, pady=(0, 5))

    listbox_container = tk.Frame(
        list_frame,
        highlightbackground="#ced4da",
        highlightthickness=1
    )
    listbox_container.pack(fill=tk.BOTH, expand=True)

    subjects_listbox = tk.Listbox(
        listbox_container,
        width=50,
        height=12,
        font=label_font,
        selectbackground=primary_color,
        activestyle="none",
        relief=tk.FLAT,
        selectmode=tk.SINGLE
    )
    subjects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(listbox_container, orient="vertical", command=subjects_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    subjects_listbox.config(yscrollcommand=scrollbar.set)

    buttons_frame = tk.Frame(main_container, bg=bg_color)
    buttons_frame.pack(fill=tk.X, pady=10)

    # -----------------------------------------

    def add_subject():
        subject = subject_entry.get().strip()
        if subject:
            subjects_listbox.insert(tk.END, subject)
            subject_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Please enter a subject name.")

    def delete_subject():
        selected_idx = subjects_listbox.curselection()
        if selected_idx:
            subjects_listbox.delete(selected_idx)
        else:
            messagebox.showwarning("Warning", "Please select a subject to delete.")

    def generate_presentation():
        subjects = subjects_listbox.get(0, tk.END)
        if subjects:
            info = list(subjects)
            print()
            generator = ImageGenerator()
            for i in info:
                generator.generate_image(i)

            progress_window = tk.Toplevel(slideshow_window)
            progress_window.title("Generating Presentation")
            progress_window.geometry("400x200")
            progress_window.configure(bg="#ffffff")
            progress_window.transient(slideshow_window)
            progress_window.grab_set()

            progress_label = tk.Label(
                progress_window,
                text="Creating your presentation...",
                font=label_font,
                bg="#ffffff"
            )
            progress_label.pack(pady=20)

            progress_bar = ttk.Progressbar(
                progress_window,
                orient="horizontal",
                length=300,
                mode="determinate"
            )
            progress_bar.pack(pady=10)

            def update_progress(value):
                if value <= 100:
                    progress_bar["value"] = value
                    progress_window.after(50, update_progress, value + 2)
                else:
                    progress_window.destroy()
                    subjects_str = ", ".join(subjects)
                    messagebox.showinfo(
                        "Presentation Generated",
                        f"Successfully created presentation with subjects:\n{subjects_str}"
                    )

            update_progress(0)
        else:
            messagebox.showwarning("Warning", "Please add at least one subject.")

    add_btn = tk.Button(
        buttons_frame,
        text="Add Subject",
        font=button_font,
        bg=primary_color,
        fg="white",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=add_subject
    )
    add_btn.pack(side=tk.LEFT, padx=5)

    delete_btn = tk.Button(
        buttons_frame,
        text="Delete Subject",
        font=button_font,
        bg="#6c757d",
        fg="white",
        relief=tk.FLAT,
        padx=10,
        pady=5,
        command=delete_subject
    )
    delete_btn.pack(side=tk.LEFT, padx=5)

    generate_frame = tk.Frame(main_container, bg=bg_color)
    generate_frame.pack(fill=tk.X, pady=10)

    generate_btn = tk.Button(
        generate_frame,
        text="Generate Presentation",
        font=("Helvetica", 12, "bold"),
        bg=secondary_color,
        fg="white",
        relief=tk.FLAT,
        padx=15,
        pady=10,
        command=generate_presentation
    )
    generate_btn.pack(fill=tk.X)


if __name__ == "__main__":
    create_stylish_tkinter_window()
