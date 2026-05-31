import os
import asyncio
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from translator_tool import adaptive_translate_tool

async def main():
    file_path = "uploads/embedded-images.pdf"
    target_lang = "de"
    
    print(f"Translating {file_path} into {target_lang.upper()}...")
    try:
        result = await adaptive_translate_tool(
            file_path=os.path.abspath(file_path),
            target_language_code=target_lang,
            source_language_code="en-US"
        )
        print("Translation success!")
        print("Result:", result)
    except Exception as e:
        print("Translation failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
