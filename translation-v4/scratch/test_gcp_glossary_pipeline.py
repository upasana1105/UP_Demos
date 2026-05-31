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

async def test_gcp_glossary_pipeline():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    location = os.getenv("TRANSLATION_LOCATION", "us-central1")
    
    original_pdf = "uploads/5g-edge-computing-value-opportunity.pdf"
    target_lang = "fr" # French
    
    lang_names = {
        "de": "German",
        "fr": "French",
        "ja": "Japanese",
        "es": "Spanish"
    }
    lang_name = lang_names.get(target_lang, target_lang)
    
    # Step 1: Scan English PDF blocks and pre-translate compactly via Gemini
    print("Scanning original PDF paragraph blocks...")
    doc = fitz.open(original_pdf)
    paragraphs = []
    for page in doc:
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text or len(text) < 15:
                continue
            if not re.search(r'[a-zA-Z]', text):
                continue
            if text.lower().replace(" ", "") in ["5g+edge", "4g+cloud", "5g+périphérie"]:
                continue
            paragraphs.append(text.replace("\n", " "))
            
    doc.close()
    
    print(f"Pre-translating {len(paragraphs)} blocks compactly into {lang_name} via Gemini...")
    client_gem = genai.Client(vertexai=True, project=project_id, location="global")
    
    glossary_pairs = []
    
    async def translate_compact(text):
        prompt = f"""
        Translate the following English slide paragraph into {lang_name}.
        You MUST keep the {lang_name} translation extremely compact, rephrased, or abbreviated so that its character count is close to or shorter than the original English text.
        
        Original English: "{text}"
        Max character length limit: {len(text) + 5} characters.
        
        Return the compact {lang_name} translation ONLY. Do not include any explanations, intro, or quotes.
        """
        try:
            response = await client_gem.aio.models.generate_content(
                model="publishers/google/models/gemini-3.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            trans_text = response.text.strip().replace('"', '').replace('\n', ' ')
            if trans_text and len(trans_text) > 2:
                glossary_pairs.append((text, trans_text))
                print(f"  Mapped: '{text[:30]}...' ➡️ '{trans_text[:30]}...'")
        except Exception as e:
            print(f"  Gemini translation failed: {e}")
            
    # Stagger task creation to prevent OAuth token contention
    tasks = []
    for p in paragraphs:
        await asyncio.sleep(0.08)
        tasks.append(asyncio.create_task(translate_compact(p)))
        
    if tasks:
        await asyncio.gather(*tasks)
        
    if not glossary_pairs:
        print("No glossary pairs created. Exiting.")
        return
        
    # Step 2: Write CSV glossary and upload to Google Cloud Storage (GCS)
    session_id = str(uuid.uuid4())[:8]
    glossary_id = f"glossary_{session_id}_{target_lang}"
    bucket_name = f"{project_id}-dynamic-glossaries"
    csv_filename = f"{glossary_id}.csv"
    
    print(f"Generating CSV glossary: {csv_filename}...")
    csv_content = ""
    for src, tgt in glossary_pairs:
        # Standard GCP Glossary CSV format: SourceTerm,TargetTerm
        # Escape double quotes to comply with standard RFC 4180 CSV formatting
        src_escaped = src.replace('"', '""')
        tgt_escaped = tgt.replace('"', '""')
        csv_content += f'"{src_escaped}","{tgt_escaped}"\n'
        
    # Upload CSV to GCS bucket dynamically
    print(f"Uploading to bucket: gs://{bucket_name}/{csv_filename}...")
    storage_client = storage.Client()
    # Ensure the storage bucket exists, create it if not
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        bucket = storage_client.create_bucket(bucket_name, location="us-central1")
        
    blob = bucket.blob(csv_filename)
    blob.upload_from_string(csv_content, content_type="text/csv")
    
    # Step 3: Register standard Glossary resource natively in GCP
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
    
    # Step 4: Run standard Translation API Advanced translate_document with Glossary
    print("Running standard Translate API Advanced translate_document natively...")
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
        
        output_pdf = f"uploads/5g-edge-computing-value-opportunity_{target_lang}_glossary.pdf"
        with open(output_pdf, "wb") as f:
            f.write(translated_pdf_bytes)
        print(f"🎉 Document translated successfully! Saved natively to {output_pdf}")
    except Exception as e:
        print(f"Translation failed: {e}")
    finally:
        # Step 5: Clean up temporary GCS and Glossary resources cleanly
        print("Cleaning up GCS and Glossary resources...")
        try:
            blob.delete()
            delete_operation = translate_client.delete_glossary(name=f"{parent}/glossaries/{glossary_id}")
            delete_operation.result(timeout=90)
            print("Cleanup completed cleanly!")
        except Exception as clean_err:
            print(f"Cleanup warning: {clean_err}")

if __name__ == "__main__":
    asyncio.run(test_gcp_glossary_pipeline())
