import os
import fitz
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_new_model():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    doc = fitz.open("uploads/5g-edge-computing-value-opportunity.pdf")
    page = doc[0]
    width = page.rect.width
    height = page.rect.height
    rect = fitz.Rect(0, height * 0.4, width, height)
    pix = page.get_pixmap(clip=rect, dpi=300)
    img_bytes = pix.tobytes("png")
    
    prompt = """
    Translate ALL text within this image into French.
    It is CRITICAL that every single word, label, title, and legend item is translated to French. Do NOT leave any text in English.
    Translate 'Technology' to 'Technologie', 'Aerospace & defence' to 'Aéronautique & défense', 'Finance' to 'Finance', 'Logistics' to 'Logistique', 'Retail' to 'Vente au détail', 'Pharma' to 'Pharmaceutique'.
    Generate a new image that is identical in style, layout, colors, and data presentation as the input image, but with the fully translated French text.
    """
    
    for model_name in ["gemini-3.1-flash-image", "gemini-3-pro-image"]:
        print(f"Calling model {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    types.Part.from_text(text=prompt)
                ]
            )
            # The custom model in this env returns raw bytes or standard response
            # Let's check type
            print(f"  Response Type: {type(response)}")
            if isinstance(response, bytes):
                output_path = f"uploads/test_new_model_{model_name.split('/')[-1]}.png"
                with open(output_path, "wb") as f:
                    f.write(response)
                print(f"  Success! Saved to {output_path}")
            else:
                new_img_bytes = None
                for part in response.candidates[0].content.parts:
                    try:
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            new_img_bytes = part.inline_data.data
                            break
                    except AttributeError:
                        pass
                if new_img_bytes:
                    output_path = f"uploads/test_new_model_{model_name.split('/')[-1]}.png"
                    with open(output_path, "wb") as f:
                        f.write(new_img_bytes)
                    print(f"  Success! Saved to {output_path}")
                else:
                    print("  Failed: No image in response")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    test_new_model()
