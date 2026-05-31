import os
import fitz
import re
import asyncio
import uuid
from google.cloud import translate_v3 as translate
from google.cloud import storage
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_sentence_glossary():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    location = os.getenv("TRANSLATION_LOCATION", "us-central1")
    
    original_pdf = "uploads/1a-ai-and-model-risk-slipsheet.pdf"
    target_lang = "fr" # French
    
    lang_names = {"de": "German", "fr": "French", "ja": "Japanese", "es": "Spanish"}
    lang_name = lang_names.get(target_lang, target_lang)
    
    # Step 1: Scan English PDF text-rich spans (sentences/lines)
    print("Scanning original PDF spans...")
    doc = fitz.open(original_pdf)
    spans_text = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        text = s["text"].strip()
                        # Skip bullets, digits, or page numbers
                        if len(text) < 8 or not re.search(r'[a-zA-Z]', text):
                            continue
                        # Avoid duplicates in glossary
                        clean_text = text.replace("\n", " ")
                        if clean_text not in spans_text:
                            spans_text.append(clean_text)
    doc.close()
    
    print(f"Pre-translating {len(spans_text)} spans compactly into {lang_name} via Gemini...")
    client_gem = genai.Client(vertexai=True, project=project_id, location="global")
    glossary_pairs = []
    
    sem = asyncio.Semaphore(3) # Limit to 3 concurrent active requests
    
    async def translate_compact(text):
        prompt = f"""
        Translate the following English slide text span into {lang_name}.
        You MUST keep the {lang_name} translation extremely compact, rephrased, or abbreviated so that its character count is close to or shorter than the original English text.
        
        Original English: "{text}"
        Max character length limit: {len(text) + 3} characters.
        
        Return the compact {lang_name} translation ONLY. Do not include any explanations or quotes.
        """
        async with sem:
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = await client_gem.aio.models.generate_content(
                        model="publishers/google/models/gemini-3.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    trans_text = response.text.strip().replace('"', '').replace('\n', ' ')
                    if trans_text and len(trans_text) > 2:
                        glossary_pairs.append((text, trans_text))
                        print(f"  Mapped: '{text[:25]}...' ➡️ '{trans_text[:25]}...'")
                    break
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "resource_exhausted" in str(e):
                        import random
                        sleep_delay = (2 ** attempt) + random.uniform(0.3, 0.9)
                        print(f"Rate limit 429 hit. Retrying span in {sleep_delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(sleep_delay)
                    else:
                        print(f"  Gemini failed for span: {e}")
                        break
            
    tasks = []
    for t in spans_text:
        tasks.append(asyncio.create_task(translate_compact(t)))
    if tasks:
        await asyncio.gather(*tasks)
        
    if not glossary_pairs:
        print("No glossary pairs created. Exiting.")
        return
        
    # Step 2: Compile and upload CSV glossary to GCS
    session_id = str(uuid.uuid4())[:8]
    glossary_id = f"glossary_{session_id}_{target_lang}"
    bucket_name = f"{project_id}-dynamic-glossaries"
    csv_filename = f"{glossary_id}.csv"
    
    print(f"Uploading CSV glossary gs://{bucket_name}/{csv_filename}...")
    csv_content = ""
    for src, tgt in glossary_pairs:
        src_escaped = src.replace('"', '""')
        tgt_escaped = tgt.replace('"', '""')
        csv_content += f'"{src_escaped}","{tgt_escaped}"\n'
        
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        bucket = storage_client.create_bucket(bucket_name, location="us-central1")
    blob = bucket.blob(csv_filename)
    blob.upload_from_string(csv_content, content_type="text/csv")
    
    # Step 3: Register GCP Glossary resource natively
    print(f"Registering standard GCP Glossary resource: {glossary_id}...")
    translate_client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"
    
    glossary_resource = {
        "name": f"{parent}/glossaries/{glossary_id}",
        "language_pair": {
            "source_language_code": "en",
            "target_language_code": target_lang
        },
        "input_config": {
            "gcs_source": {
                "input_uri": f"gs://{bucket_name}/{csv_filename}"
            }
        }
    }
    
    create_operation = translate_client.create_glossary(parent=parent, glossary=glossary_resource)
    print("Waiting for GCP Glossary compilation operation (takes ~25s)...")
    create_operation.result(timeout=120)
    print(f"🎉 GCP Glossary registered successfully: {glossary_id}")
    
    # Step 4: Translate PDF natively with Glossary
    print("Running standard Translation API Advanced translate_document natively...")
    with open(original_pdf, "rb") as f:
        pdf_content = f.read()
        
    request = {
        "parent": parent,
        "target_language_code": target_lang,
        "source_language_code": "en",
        "document_input_config": {
            "content": pdf_content,
            "mime_type": "application/pdf"
        },
        "glossary_config": {
            "glossary": f"{parent}/glossaries/{glossary_id}"
        }
    }
    
    try:
        response = translate_client.translate_document(request=request)
        translated_pdf_bytes = response.document_translation.byte_stream_outputs[0]
        
        output_pdf = f"uploads/1a-ai-and-model-risk-slipsheet_{target_lang}_sentenceglossary.pdf"
        with open(output_pdf, "wb") as f:
            f.write(translated_pdf_bytes)
        print(f"🎉 PDF translated natively! Saved to {output_pdf}")
    except Exception as e:
        print(f"Translation failed: {e}")
    finally:
        # Step 5: Cleanup GCS and Glossary
        print("Cleaning up GCS and Glossary resources...")
        try:
            blob.delete()
            delete_operation = translate_client.delete_glossary(name=f"{parent}/glossaries/{glossary_id}")
            delete_operation.result(timeout=90)
            print("Cleanup complete!")
        except Exception as clean_err:
            print(f"Cleanup warning: {clean_err}")

if __name__ == "__main__":
    asyncio.run(test_sentence_glossary())
