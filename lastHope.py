import tkinter as tk
from tkinter import PhotoImage
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
script_dir = os.path.dirname(os.path.abspath(__file__))



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
    def __init__(self, root, image_folder):
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

        if self.image_files:
            self.show_image()

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


# Main execution
if __name__ == "__main__":
    root = tk.Tk()

    # Create folders if they don't exist
    os.makedirs("generated_images", exist_ok=True)
    os.makedirs("new_generated", exist_ok=True)

    # Create an instance of PhotoViewer
    image_folder = "./generated_images"  # Replace with the path to your image folder
    viewer = PhotoViewer(root, image_folder)

    root.mainloop()