import os
import fitz
from google.cloud import translate_v3 as translate
from google.api_core.exceptions import InvalidArgument, GoogleAPICallError

def run_tests():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    location = os.getenv("TRANSLATION_LOCATION", "us-central1")
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"

    input_file = "sample_doc.pdf"
    if not os.path.exists(input_file):
        input_file = os.path.join(os.path.dirname(__file__), "..", "sample_doc.pdf")

    with open(input_file, "rb") as f:
        content = f.read()

    os.makedirs("uploads", exist_ok=True)

    print(f"=== Project: {project_id}, Location: {location} ===")
    print(f"Input file: {input_file} ({len(content)} bytes)\n")

    test_cases = [
        ("default (not set)", None, "uploads/test_default.pdf"),
        ("NO_ATTRIBUTION", "NO_ATTRIBUTION", "uploads/test_no_attribution.pdf"),
        ("Machine Translated by Google Cloud", "Machine Translated by Google Cloud", "uploads/test_google_cloud.pdf"),
        ("invalid: 'Translated by My Company'", "Translated by My Company", None),
        ("invalid: 'Translated by KPMG'", "Translated by KPMG", None),
    ]

    for label, attr_val, out_path in test_cases:
        print(f"--- Testing Case: {label} ---")
        request = {
            "parent": parent,
            "target_language_code": "es",
            "source_language_code": "en",
            "document_input_config": {
                "content": content,
                "mime_type": "application/pdf",
            },
        }
        if attr_val is not None:
            request["customized_attribution"] = attr_val

        try:
            response = client.translate_document(request=request)
            print("  Status: SUCCESS")
            if out_path:
                translated_bytes = response.document_translation.byte_stream_outputs[0]
                with open(out_path, "wb") as out_f:
                    out_f.write(translated_bytes)
                print(f"  Saved to: {out_path} ({len(translated_bytes)} bytes)")
                
                doc = fitz.open(out_path)
                page = doc[0]
                text = page.get_text("text")
                first_lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
                print(f"  First text lines on page: {first_lines}")
                has_watermark = any("Machine Translated" in line for line in text.split("\n"))
                print(f"  Contains 'Machine Translated': {has_watermark}")
                doc.close()
        except InvalidArgument as e:
            print(f"  Status: REJECTED (Expected 400 InvalidArgument)")
            print(f"  Error message: {e.message}")
        except GoogleAPICallError as e:
            print(f"  Status: API ERROR ({e.code})")
            print(f"  Error message: {e.message}")
        except Exception as e:
            print(f"  Status: UNEXPECTED ERROR: {e}")
        print()

if __name__ == "__main__":
    run_tests()
