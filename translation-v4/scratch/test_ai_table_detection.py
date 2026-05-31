import os
import asyncio
import sys
import json
import re

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fitz
from google import genai
from google.genai import types

async def main():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    doc = fitz.open("uploads/0000646.pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=300) # High resolution 300 DPI
    img_bytes = pix.tobytes("png")
    
    detect_prompt = """
    Locate the main data table on this page.
    Return the table bounding box and column boundaries as a JSON object with values normalized from 0 to 1000:
    {
      "ymin": 150,
      "xmin": 30,
      "ymax": 950,
      "xmax": 970,
      "columns": [30, 220, 410, 580, 760, 970]
    }
    Where:
    - 'columns' lists the X-coordinates of the vertical grid lines separating columns (including left and right table edges).
    If no table exists on this page, return {"no_table": true}.
    Return ONLY valid JSON, no code blocks.
    """
    
    print("Calling gemini-2.5-flash to detect table and columns on Page 0...")
    try:
        def sync_call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    types.Part.from_text(text=detect_prompt)
                ]
            )
        response = await asyncio.to_thread(sync_call)
        print("Response Text:")
        print(response.text)
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            print("Parsed JSON Data:")
            print(data)
    except Exception as e:
        print("AI call failed:", e)
        
    doc.close()

if __name__ == "__main__":
    asyncio.run(main())
