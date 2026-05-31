import sys
import os
from dotenv import load_dotenv

# Load env vars if needed
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from translator_tool import localize_images_in_pdf

pdf_path = '/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation-v3/uploads/5g-edge-computing-value-opportunity_de.pdf'
target_lang = 'de'

print("Starting localization test...")
localize_images_in_pdf(pdf_path, target_lang)
print("Finished localization test.")
