import os
import fitz
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_gemini_image():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    # Render the bubble chart from the original PDF
    doc = fitz.open("uploads/5g-edge-computing-value-opportunity.pdf")
    page = doc[0]
    width = page.rect.width
    height = page.rect.height
    rect = fitz.Rect(0, height * 0.4, width, height)
    pix = page.get_pixmap(clip=rect, dpi=300)
    img_bytes = pix.tobytes("png")
    
    print(f"Rendered chart image size: {len(img_bytes)} bytes")
    
    target_lang = "ja"
    prompt = f"""
    Translate ALL text within this image into target language code '{target_lang}'.
    It is CRITICAL that every single word, label, title, and legend item is translated to target language code '{target_lang}'.
    Do NOT leave any text in English. For example, translate 'Technology' to 'テクノロジー', 'Aerospace & defence' to '航空宇宙・防衛', 'Transport / Mobility' to '運輸・モビリティ', 'Finance' to '金融', 'Insurance' to '保険', etc.
    Generate a new image that is identical in style, layout, colors, and data presentation as the input image, but with the fully translated text.
    Ensure high visual fidelity, crisp text, and correct label alignments next to bubbles/graphics.
    """
    
    print("Calling gemini-2.5-flash-image...")
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            types.Part.from_text(text=prompt)
        ]
    )
    
    print("Response Candidates:")
    for i, candidate in enumerate(response.candidates):
        print(f"Candidate {i}:")
        print(f"  Finish Reason: {candidate.finish_reason}")
        print(f"  Parts count: {len(candidate.content.parts)}")
        for j, part in enumerate(candidate.content.parts):
            print(f"    Part {j}:")
            if part.text:
                print(f"      Text: {part.text[:200]}...")
            elif part.inline_data:
                print(f"      Inline Data MIME: {part.inline_data.mime_type}")
                print(f"      Inline Data Length: {len(part.inline_data.data)} bytes")
                # Save the generated image to see if it is translated!
                with open("uploads/test_gemini_output_ja.png", "wb") as f:
                    f.write(part.inline_data.data)
                print("      Saved output image to uploads/test_gemini_output_ja.png")

if __name__ == "__main__":
    test_gemini_image()
