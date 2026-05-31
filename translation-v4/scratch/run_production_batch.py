import os
import asyncio
import glob
import shutil
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from translator_tool import adaptive_translate_tool

async def run_batch():
    decks = [
        "uploads/5g-edge-computing-value-opportunity.pdf",
        "uploads/22-7360-successful-spins-final-0429-update-secured.pdf",
        "uploads/22-6898-ukraine-strategy-under-uncertainty.pdf"
    ]
    # Target languages: German, Spanish, French, Japanese
    languages = ["de", "es", "fr", "ja"]
    
    print("Starting Production Batch Translation Pipeline...")
    for deck in decks:
        for lang in languages:
            print(f"\n--- Translating {deck} into {lang.upper()} ---")
            try:
                result = await adaptive_translate_tool(
                    file_path=os.path.abspath(deck),
                    target_language_code=lang,
                    source_language_code="en-US"
                )
                print(f"Result: {result}")
            except Exception as e:
                print(f"Failed to translate {deck} into {lang}: {e}")
                
    # Clean up all temporary, cached, and intermediate files to keep uploads folder pristine
    print("\nRunning intermediate files cleanup...")
    temp_extensions = [
        "uploads/*_compacted.pdf",
        "uploads/*_typotemp.pdf",
        "uploads/*_temp.pdf",
        "uploads/*.png",
        "uploads/*.webp",
        "uploads/test_*.pdf",
        "uploads/test_*.png"
    ]
    for pattern in temp_extensions:
        for filepath in glob.glob(pattern):
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
                    
    print("🎉 Production Batch Translation Pipeline completed cleanly!")

if __name__ == "__main__":
    asyncio.run(run_batch())
