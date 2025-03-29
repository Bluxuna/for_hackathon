import datetime
import time
import os
import uuid
from PIL import Image
import requests

class ImageGenerator:
    """
    Generates images from prompts using Pollinations AI, with error handling and cropping.
    """

    def __init__(self, save_path="generated_images"):
        """
        Initializes the ImageGenerator with a save path.
        """
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)

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

    def generate_image(self, prompt,i):
        """
        Generates an image from a prompt, downloads it, crops it, and returns the path.
        """
        formatted_prompt = self._generate_unique_prompt(prompt)
        url = f"https://image.pollinations.ai/prompt/{formatted_prompt}"

        while True:
            image_save_name = f"img_{i}.png"
            image_save_path = os.path.join(self.save_path, image_save_name)

            if self._download_and_save_image(url, image_save_path):
                if self._crop_image(image_save_path):
                    return image_save_path

            print("Retrying image generation...")
            time.sleep(5)

if __name__ == "__main__":
    prompts = ["give me abstract image with text of COPE in the center and below that write hello ",
               "paper based presentation with mini images on it",
               "slide show style presentation",
               "Artificial inteligence robots",
               "live time visualisation"]
    generator = ImageGenerator()

    for i in range(len(prompts)):
        image_path = generator.generate_image(prompts[i],i)
        print(f"Generated: {image_path}")