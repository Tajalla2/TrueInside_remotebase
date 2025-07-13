import easyocr
from PIL import Image
import os
import numpy as np


reader = easyocr.Reader(["en"])


def extract_ingredients(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Open with PIL and convert to NumPy array
    img = Image.open(image_path).convert("RGB")  # handles PNG transparency
    img_np = np.array(img)

    # Run EasyOCR
    results = reader.readtext(img_np, detail=0)

    # Optional: post-process to extract ingredients
    return results


# o = ocr()
# ingredients = o.extract_ingredients(
#     r"D:\Projects\TrueInside_remotebase\chatbot\chatlogic\image.png"
# )
