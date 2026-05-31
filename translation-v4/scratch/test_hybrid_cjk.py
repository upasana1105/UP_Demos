import os
import fitz
import shutil
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_hybrid_engine():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    # Paths
    original_pdf = "uploads/5g-edge-computing-value-opportunity.pdf"
    # Let's assume we already have standard Translate API output for Japanese
    # In the real backend, this is the translated PDF output from translate_document()
    translated_pdf = "uploads/5g-edge-computing-value-opportunity_ja_final.pdf"
    final_pdf = "uploads/5g-edge-computing-value-opportunity_ja_hybrid.pdf"
    
    # Step 1: Copy original CJK-font-embedded translated PDF to final path
    if os.path.exists(final_pdf):
        os.remove(final_pdf)
    shutil.copy(translated_pdf, final_pdf)
    
    doc_orig = fitz.open(original_pdf)
    doc_trans = fitz.open(final_pdf)
    
    print("Scanning translated PDF spans for shrunked font sizes...")
    for page_num in range(len(doc_orig)):
        page_orig = doc_orig[page_num]
        page_trans = doc_trans[page_num]
        
        orig_spans = []
        trans_spans = []
        
        # Collect original spans
        blocks_orig = page_orig.get_text("dict")["blocks"]
        for b in blocks_orig:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        orig_spans.append(s)
                        
        # Collect translated spans
        blocks_trans = page_trans.get_text("dict")["blocks"]
        for b in blocks_trans:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        trans_spans.append(s)
                        
        # Map translated spans by overlap coordinates
        for ts in trans_spans:
            ts_rect = fitz.Rect(ts["bbox"])
            ts_text = ts["text"].strip()
            if not ts_text or len(ts_text) < 2:
                continue
                
            # Skip bullet points or list items to be safe
            if not re.search(r'[a-zA-Z\u3040-\u309f\u30a0-\u30ff\uff00-\uffef\u4e00-\u9faf]', ts_text):
                continue
                
            # Find original matching span
            matching_os = None
            best_overlap = 0.0
            for os_span in orig_spans:
                os_rect = fitz.Rect(os_span["bbox"])
                intersect = ts_rect.intersect(os_rect)
                if not intersect.is_empty:
                    overlap_area = intersect.get_area()
                    if overlap_area > best_overlap:
                        best_overlap = overlap_area
                        matching_os = os_span
                        
            if matching_os:
                os_text = matching_os["text"].strip()
                orig_size = matching_os["size"]
                trans_size = ts["size"]
                
                # If translation shrunked font size (indicating it was too long to fit coordinates)
                if trans_size < (orig_size - 1.0) and orig_size > 6.0:
                    print(f"  Found shrunked span: '{ts_text}' (Size: {trans_size:.1f} < Orig: {orig_size:.1f})")
                    print(f"    Original English: '{os_text}'")
                    
                    # Ask Gemini to generate compact translation matching English length
                    prompt = f"""
                    Translate the following short English phrase into Japanese.
                    You MUST keep the Japanese translation extremely compact, rephrased, or abbreviated so that its character length is close to or shorter than the original English text.
                    
                    Original English: "{os_text}"
                    Literal Translation: "{ts_text}"
                    Max character length limit: {len(os_text) + 3} characters.
                    
                    Return the compact Japanese translation ONLY.
                    """
                    
                    try:
                        response = client.models.generate_content(
                            model="publishers/google/models/gemini-3.5-flash",
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=0.0)
                        )
                        compact_text = response.text.strip().replace('"', '')
                        print(f"    Gemini Compact Japanese: '{compact_text}' ({len(compact_text)} ch)")
                        
                        # Sample background color dynamically for seamless coverage
                        clip_rect = fitz.Rect(ts_rect.x0 - 1, ts_rect.y0 - 1, ts_rect.x0 + 1, ts_rect.y0 + 1)
                        pix = page_trans.get_pixmap(clip=clip_rect, dpi=72)
                        rgb_pixel = pix.pixel(0, 0)
                        bg_color = (rgb_pixel[0]/255.0, rgb_pixel[1]/255.0, rgb_pixel[2]/255.0)
                        
                        # Draw seamless cover-up rectangle over the shrunked span
                        expanded_rect = fitz.Rect(ts_rect.x0 - 1, ts_rect.y0 - 1, ts_rect.x1 + 1, ts_rect.y1 + 1)
                        page_trans.draw_rect(expanded_rect, color=bg_color, fill=bg_color)
                        
                        # Sample original text color
                        r = (matching_os["color"] >> 16 & 255) / 255.0
                        g = (matching_os["color"] >> 8 & 255) / 255.0
                        b = (matching_os["color"] & 255) / 255.0
                        
                        # Draw new compact Japanese text block using the PDF's native CJK font!
                        page_trans.insert_text(
                            fitz.Point(ts_rect.x0, ts_rect.y0 + ts_rect.height * 0.8),
                            compact_text,
                            fontsize=orig_size,
                            color=(r, g, b),
                            fontname=ts["font"]  # Standard native CJK font already in PDF!
                        )
                    except Exception as e:
                        print(f"    Failed to replace block: {e}")
                        
    doc_trans.save("uploads/5g-edge-computing-value-opportunity_ja_hybrid_final.pdf")
    doc_trans.close()
    doc_orig.close()
    shutil.move("uploads/5g-edge-computing-value-opportunity_ja_hybrid_final.pdf", final_pdf)
    print(f"🎉 Hybrid CJK Layout Correction complete! Saved to {final_pdf}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_hybrid_engine())
