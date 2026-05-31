import os
from google.cloud import translate_v3 as translate
from dotenv import load_dotenv

load_dotenv()

def test_translate():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    location = "us-central1"
    
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"
    
    file_path = "uploads/5g-edge-computing-value-opportunity.pdf"
    with open(file_path, "rb") as f:
        content = f.read()
        
    document_input_config = {
        "content": content,
        "mime_type": "application/pdf",
    }
    
    request = {
        "parent": parent,
        "target_language_code": "ja",
        "source_language_code": "en-US",
        "document_input_config": document_input_config,
    }
    
    response = client.translate_document(request=request)
    translated_content = response.document_translation.byte_stream_outputs[0]
    
    output_path = "uploads/test_gcp_raw_ja.pdf"
    with open(output_path, "wb") as f:
        f.write(translated_content)
    print(f"Saved raw GCP translation to {output_path}")

if __name__ == "__main__":
    test_translate()
