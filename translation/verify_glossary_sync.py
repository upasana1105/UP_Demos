from google.cloud import translate_v3 as translate
import os

def check_glossary_enforcement():
    project_id = "uppdemos"
    location = "us-central1"
    glossary_id = "kpmg-5g-german"
    
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"
    glossary = f"{parent}/glossaries/{glossary_id}"
    
    glossary_config = translate.TranslateTextGlossaryConfig(glossary=glossary)
    
    test_strings = [
        "with US$4.3 trillion of upside",
        "4.3 trillion",
        "trillion"
    ]
    
    print(f"--- Verifying Glossary: {glossary_id} ---")
    for text in test_strings:
        response = client.translate_text(
            request={
                "contents": [text],
                "target_language_code": "de",
                "source_language_code": "en",
                "parent": parent,
                "glossary_config": glossary_config,
            }
        )
        translation = response.glossary_translations[0].translated_text
        print(f"Source: '{text}' -> Translation: '{translation}'")

if __name__ == "__main__":
    check_glossary_enforcement()
