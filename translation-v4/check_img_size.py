from PIL import Image
import sys

img_path = '/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation-v3/debug_images/page_0_image_6.png'
try:
    img = Image.open(img_path)
    print(f"Image size: {img.size}")
except Exception as e:
    print(f"Error: {e}")
