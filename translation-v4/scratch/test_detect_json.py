import os
import fitz
import re
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_detect_json():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    doc = fitz.open("uploads/5g-edge-computing-value-opportunity.pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=300)
    img_bytes = pix.tobytes("png")
    
    detect_prompt = """
    Identify the bounding box of the main table on this page. 
    Return the coordinates as a JSON object with normalized values from 0 to 1000:
    {"ymin": 200, "xmin": 50, "ymax": 800, "xmax": 950}
    If no table exists, return {"no_table": true}.
    """
    
    print("Calling gemini-2.5-flash for table detection...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            types.Part.from_text(text=detect_prompt)
        ],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )
    )
    
    print(f"Raw Response Text: {repr(response.text)}")
    
    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if json_match:
        print(f"Matched JSON String: {repr(json_match.group(0))}")
        try:
            data = json.loads(json_match.group(0))
            print(f"Successfully parsed JSON: {data}")
        except Exception as e:
            print(f"JSON Parsing Failed: {e}")
    else:
        print("No JSON match found in response text.")

if __name__ == "__main__":
    test_detect_json()
