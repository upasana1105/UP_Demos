import os
import fitz
import shutil
import re
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def pre_compact_english_pdf(original_pdf: str, compacted_pdf: str):
    """Surgically rephrases verbose English paragraphs inside the original PDF to be extremely concise before translation."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    client = genai.Client(vertexai=True, project=project_id, location="global")
    
    if os.path.exists(compacted_pdf):
        os.remove(compacted_pdf)
    shutil.copy(original_pdf, compacted_pdf)
    
    doc_orig = fitz.open(original_pdf)
    doc_compact = fitz.open(compacted_pdf)
    
    print("Pre-compacting English paragraph blocks...")
    for page_num in range(len(doc_orig)):
        page_orig = doc_orig[page_num]
        page_compact = doc_compact[page_num]
        
        # Collect original blocks
        blocks_orig = page_orig.get_text("blocks")
        
        # Temporary storage for this page's rephrased blocks to avoid concurrent PDF write collisions
        page_results = []
        
        async def compact_ob_block(ob, page_orig):
            tb_rect = fitz.Rect(ob[:4])
            ob_text = ob[4].strip()
            if not ob_text or len(ob_text) < 10:
                return
                
            # Skip bullets and brands
            if not re.search(r'[a-zA-Z]', ob_text):
                return
            if ob_text.lower().replace(" ", "") in ["5g+edge", "4g+cloud", "5g+périphérie"]:
                return
                
            # Get font size and color of first span inside this block
            orig_size = 10.0
            ts_font = "helv"
            text_color = (0.1, 0.1, 0.1)
            
            orig_page_dict = page_orig.get_text("dict")
            for b in orig_page_dict["blocks"]:
                b_rect = fitz.Rect(b["bbox"])
                if b_rect.intersect(tb_rect).get_area() > (tb_rect.get_area() * 0.8) and "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            font_lower = s["font"].lower()
                            if "bold" in font_lower or "black" in font_lower or "heavy" in font_lower or "medium" in font_lower:
                                ts_font = "Helvetica-Bold"
                            else:
                                ts_font = "Helvetica"
                            orig_size = s["size"]
                            r = (s["color"] >> 16 & 255) / 255.0
                            g = (s["color"] >> 8 & 255) / 255.0
                            b_val = (s["color"] & 255) / 255.0
                            text_color = (r, g, b_val)
                            break
                        break
                    break
            
            # If the paragraph is dense (e.g., has multiple lines or > 100 chars), compact it!
            if len(ob_text) > 80:
                ob_text_clean = ob_text.replace('\n', ' ')
                # Ask Gemini to rephrase English paragraph to be extremely concise natively
                prompt = f"""
                You are a professional copywriter.
                The following slide paragraph is too verbose and will cause layout overlaps or tiny shrunked font sizes when translated into Spanish/German.
                
                Original English Paragraph: "{ob_text_clean}"
                
                Your job is to rewrite this English paragraph to be extremely concise, short, and compact, while preserving 100% of its original data points, key metrics, meaning, and professional tone.
                - Make sure it is at least 25% shorter in character count.
                - Keep it under {int(len(ob_text) * 0.75)} characters.
                
                Return the compact English paragraph ONLY. Do not include any explanations, intro, or quotes.
                """
                
                try:
                    response = await client.aio.models.generate_content(
                        model="publishers/google/models/gemini-3.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    compact_text = response.text.strip().replace('"', '')
                    print(f"  Page {page_num} | Rephrased: '{ob_text_clean[:40]}...' ➡️ '{compact_text[:40]}...'")
                    
                    # Sample background color
                    clip_rect = fitz.Rect(tb_rect.x0 - 1, tb_rect.y0 - 1, tb_rect.x0 + 1, tb_rect.y0 + 1)
                    pix = page_orig.get_pixmap(clip=clip_rect, dpi=72)
                    rgb_pixel = pix.pixel(0, 0)
                    bg_color = (rgb_pixel[0]/255.0, rgb_pixel[1]/255.0, rgb_pixel[2]/255.0)
                    
                    expanded_rect = fitz.Rect(tb_rect.x0 - 2, tb_rect.y0 - 2, tb_rect.x1 + 2, tb_rect.y1 + 2)
                    page_results.append((expanded_rect, compact_text, orig_size, ts_font, text_color, bg_color))
                except Exception as e:
                    print(f"  Failed to compact block on page {page_num}: {e}")
                    
        span_tasks = []
        for ob in blocks_orig:
            await asyncio.sleep(0.08)
            span_tasks.append(asyncio.create_task(compact_ob_block(ob, page_orig)))
            
        if span_tasks:
            await asyncio.gather(*span_tasks)
            
        # Perform all PDF structural writes in a single clean thread-safe loop per page!
        if page_results:
            # Step A: Add all redact annotations first
            for expanded_rect, _, _, _, _, bg_color in page_results:
                page_compact.add_redact_annot(expanded_rect, fill=bg_color)
                
            # Step B: Apply all page redactions at once (completely purging old stream!)
            page_compact.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            # Step C: insert new textbox annotations seamlessly
            for expanded_rect, compact_text, orig_size, ts_font, text_color, _ in page_results:
                page_compact.insert_textbox(
                    expanded_rect,
                    compact_text,
                    fontsize=orig_size,
                    fontname=ts_font,
                    color=text_color
                )
            
    doc_compact.save("uploads/pre_compact_temp_final.pdf")
    doc_compact.close()
    doc_orig.close()
    shutil.move("uploads/pre_compact_temp_final.pdf", compacted_pdf)
    print(f"🎉 Pre-compacting complete! Saved to {compacted_pdf}")

async def run_test():
    original_pdf = "uploads/22-7360-successful-spins-final-0429-update-secured.pdf"
    compacted_pdf = "uploads/22-7360-successful-spins-final-0429-update-secured_compacted.pdf"
    await pre_compact_english_pdf(original_pdf, compacted_pdf)

if __name__ == "__main__":
    asyncio.run(run_test())
