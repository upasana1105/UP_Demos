import os
import fitz
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_gemini_image_french():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    doc = fitz.open("uploads/5g-edge-computing-value-opportunity.pdf")
    page = doc[0]
    width = page.rect.width
    height = page.rect.height
    rect = fitz.Rect(0, height * 0.4, width, height)
    pix = page.get_pixmap(clip=rect, dpi=300)
    img_bytes = pix.tobytes("png")
    
    target_lang = "fr"
    prompt = f"""
    Translate ALL text within this image into target language French ('{target_lang}').
    It is CRITICAL that every single word, label, title, and legend item is translated to '{target_lang}'.
    
    SPECIFIC TRANSLATION RULES FOR BUBBLES:
    - 'Technology' -> 'Technologie'
    - 'Aerospace & defence' -> 'Aéronautique & défense'
    - 'Transport / Mobility' -> 'Transport / Mobilité'
    - 'Entertainment & Media' -> 'Divertissement & médias'
    - 'Finance' -> 'Finance'
    - 'Insurance' -> 'Assurance'
    - 'Logistics' -> 'Logistique'
    - 'Professional services' -> 'Services professionnels'
    - 'Retail' -> 'Vente au détail'
    - 'Pharma' -> 'Pharmaceutique'
    - 'Utilities' -> 'Services publics'
    - 'Mining' -> 'Mines'
    - 'Manufacturing' -> 'Fabrication'
    - 'Public Sector' -> 'Secteur public'
    - 'Financial Services' -> 'Services financiers'
    - 'TMT' -> 'TMT'
    - 'Healthcare' -> 'Santé'
    - 'Industrials' -> 'Secteur industriel'
    - 'Consumer Goods & Retail' -> 'Biens de consommation & détail'
    - 'VALUE TO BE UNLOCKED' -> 'VALEUR À DÉBLOQUER'
    - 'TIME HORIZON' -> 'HORIZON TEMPOREL'
    
    Generate a new image that is identical in style, layout, colors, and data presentation as the input image, but with these translated French labels inside the bubbles.
    Ensure high visual fidelity, correct label alignment next to bubbles, and crisp text.
    """
    
    print("Calling gemini-2.5-flash-image with explicit French translation prompt...")
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            types.Part.from_text(text=prompt)
        ]
    )
    
    new_img_bytes = None
    for part in response.candidates[0].content.parts:
        try:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                new_img_bytes = part.inline_data.data
                break
        except AttributeError:
            pass
            
    if new_img_bytes:
        output_path = "uploads/test_gemini_output_explicit_fr.png"
        with open(output_path, "wb") as f:
            f.write(new_img_bytes)
        print(f"Saved output image to {output_path}")
    else:
        print("Model failed to return an image.")

if __name__ == "__main__":
    test_gemini_image_french()
