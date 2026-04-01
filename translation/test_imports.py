try:
    import google.adk
    print("ADK imported successfully.")
except ImportError:
    print("ADK import failed.")

try:
    from google.cloud import translate_v3 as translate
    print("Google Cloud Translate imported successfully.")
except ImportError:
    print("Google Cloud Translate import failed.")

try:
    from translator_tool import adaptive_translate_tool
    print("translator_tool imported successfully.")
except ImportError as e:
    print(f"translator_tool import failed: {e}")
