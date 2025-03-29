import speech_recognition as sr
import threading
import queue
import time
from Translator import Translator


# ----------------------voici unda waikitxos roca buttons davacher da mag dros daiwyos generireba
class SpeechToText:
    def __init__(self,shared_data):
        """
        Initializes the transcriber with a queue and recognizer.
        """
        self.text_queue = queue.Queue()
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.shared_data = shared_data
    def transcribe_audio(self):
        """
        Continuously transcribes Georgian audio and puts results in the queue.
        """
        try:
            with sr.Microphone() as microphone:
                self.recognizer.adjust_for_ambient_noise(microphone)
                while True:
                    try:
                        audio = self.recognizer.listen(microphone, timeout=5)
                        text = self.recognizer.recognize_google(audio, language="ka-GE")
                        self.text_queue.put(text.lower())
                    except sr.UnknownValueError:
                        self.text_queue.put("Could not understand audio.")
                    except sr.RequestError as e:
                        self.text_queue.put(f"Google Speech Recognition error: {e}")
                    except TimeoutError:
                        pass #do nothing if timeout, just continue.
                    except Exception as e:
                        self.text_queue.put(f"An unexpected error occurred: {e}")

        except Exception as e:
            self.text_queue.put(f"Microphone error: {e}")

    def write_to_file(file_name, content):
        with open(file_name, 'w') as file:
            file.write(content)

    def read_from_file(file_name):
        with open(file_name, 'r') as file:
            content = file.read()
        print(f"Read content from {file_name}:")
        print(content)
    def print_transcriptions(self):
        """
        Continuously prints transcriptions from the queue.
        """
        while True:
            try:
                text = self.text_queue.get(timeout=1)
                # print(type(text))
                text1 = self.translator.translate(text)
                self.shared_data["text"] = text1
                if text  != "Could not understand audio.":

                    with open("outputKA.txt", "a+") as file:

                        file.write('\n' + str(text))

                    with open("outputEN.txt", "a+") as file:
                        file.write('\n' + str(text1))

                print("text added")



            except queue.Empty:
                pass #do nothing if empty.

    def run(self):
        """
        Starts the transcription and printing threads.
        """
        transcription_thread = threading.Thread(target=self.transcribe_audio)
        printing_thread = threading.Thread(target=self.print_transcriptions)

        transcription_thread.daemon = True
        printing_thread.daemon = True

        transcription_thread.start()
        printing_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")




if __name__ == "__main__":
    shared_text = {}
    transcriber = SpeechToText(shared_text)

    transcriber.run()