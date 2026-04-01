import os
try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata

from typing import Optional
from google.cloud import translate_v3 as translate
from google.adk.tools.tool_context import ToolContext

def adaptive_translate_tool(
    file_path: str, 
    target_language_code: str, 
    source_language_code: Optional[str] = "en-US",
    glossary_id: Optional[str] = None,
    tool_context: ToolContext = None
) -> dict:
    """Translates a document while preserving layout using Google Cloud Translation API Advanced.

    Args:
        file_path: Absolute path to the PDF document to translate.
        target_language_code: The BCP-47 language code to translate into (e.g., 'es', 'fr').
        source_language_code: The BCP-47 language code of the source document.
        glossary_id: Optional ID of the glossary to use for consistent terminology.
        tool_context: The ADK ToolContext for accessing state and project info.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    # Document translation & glossaries require regional endpoints (e.g., us-central1), not global
    location = os.getenv("TRANSLATION_LOCATION", "us-central1") # Document translation often requires specific locations
    
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"

    # Load the document content
    try:
        with open(file_path, "rb") as document_file:
            content = document_file.read()
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file: {str(e)}"}

    document_input_config = {
        "content": content,
        "mime_type": "application/pdf",
    }

    # Prepare the request
    request = {
        "parent": parent,
        "target_language_code": target_language_code,
        "source_language_code": source_language_code,
        "document_input_config": document_input_config,
    }

    if glossary_id:
        glossary_config = {
            "glossary": f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}"
        }
        request["glossary_config"] = glossary_config

    try:
        # Note: translate_document is a synchronous call for smaller documents.
        # For batch, use batch_translate_document.
        response = client.translate_document(request=request)
        
        # The translated document is in response.document_translation.byte_stream_outputs[0]
        # But wait, translate_document returns the content directly in document_translation.
        translated_content = response.document_translation.byte_stream_outputs[0]
        
        # Save output file
        output_file_path = file_path.replace(".pdf", f"_{target_language_code}.pdf")
        with open(output_file_path, "wb") as f:
            f.write(translated_content)
        
        return {
            "status": "success", 
            "output_file": output_file_path,
            "detected_language": response.document_translation.detected_language_code
        }
    except Exception as e:
        return {"status": "error", "message": f"Translation failed: {str(e)}"}

def inspect_translation_proof(file_path: str, glossary_terms: list, source_content: Optional[str] = None) -> dict:
    """Uses Gemini to inspect the translated PDF and verify glossary enforcement with source context.
    
    Args:
        file_path: Absolute path to the translated PDF document.
        glossary_terms: List of terms expected to be preserved/translated correctly.
        source_content: Optional text of the source document to prevent false-negatives.
    """
    if not glossary_terms:
        return {
            "status": "success", 
            "audit_report": "No glossary terms were provided for this translation. Glossary enforcement check skipped."
        }

    from google import genai
    from google.genai import types
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "uppdemos")
    location = "global"
    
    client = genai.Client(vertexai=True, project=project_id, location=location)
    
    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
            
        prompt = f"""You are an AI Auditor for Financial Translations. 
Review the attached translated PDF document. 

### CONTEXT
- **Expected Glossary Terms**: {", ".join(glossary_terms)}
- **Original Source Text (for reference)**: {source_content[:5000] if source_content else "Not provided"}

### YOUR MISSION
1. Verify if the 'Expected Glossary Terms' were strictly followed in the translated PDF.
2. **CRITICAL**: If a glossary term is not present in the 'Original Source Text', IGNORE it. Do not report it as a failure if it wasn't in the source.
3. For terms that ARE in the source, confirm if they were correctly preserved or localized in the output.
"""
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        return {"status": "success", "audit_report": response.text}
    except Exception as e:
        return {"status": "error", "message": f"AI Audit failed: {str(e)}"}

def read_csv_glossary(file_path: str) -> dict:
    """Reads a custom CSV glossary to understand terminology enforcement.
    
    Args:
        file_path: Absolute path to the CSV glossary file.
    """
    import csv
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Glossary file not found at {file_path}"}
    
    terms = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    terms.append(" -> ".join(row))
        return {"status": "success", "terms": terms}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def save_dynamic_glossary(terms: list, filename: str = "dynamic_glossary.csv") -> dict:
    """Saves a list of terminology mappings to a temporary CSV glossary.
    
    Args:
        terms: List of strings in 'SourceTerm,TargetTerm' format.
        filename: Name of the temporary glossary file.
    """
    import csv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    glossary_dir = os.path.join(base_dir, "glossaries")
    os.makedirs(glossary_dir, exist_ok=True)
    
    file_path = os.path.join(glossary_dir, filename)
    try:
        with open(file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for term in terms:
                if "," in term:
                    writer.writerow(term.split(",", 1))
                else:
                    writer.writerow([term, term]) # Preserve if no mapping
        return {"status": "success", "file_path": os.path.abspath(file_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
