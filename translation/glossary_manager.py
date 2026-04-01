import os
from google.cloud import storage
from google.cloud import translate_v3 as translate

def create_cloud_glossary(local_csv_path: str, target_language: str, project_id: str = "uppdemos", location: str = "us-central1", bucket_name: str = "uppdemos") -> str:
    """Uploads a CSV to GCS and registers it as a Cloud Translation Glossary."""
    
    # 1. Upload to GCS
    filename = os.path.basename(local_csv_path)
    glossary_id = filename.replace('.csv', '').replace('_', '-').lower()
    gcs_path = f"gs://{bucket_name}/glossaries/{filename}"
    
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"glossaries/{filename}")
    
    print(f"Uploading {local_csv_path} to {gcs_path}...")
    blob.upload_from_filename(local_csv_path)
    print("Upload complete.")

    # 2. Register Glossary with Translation API
    client = translate.TranslationServiceClient()
    name = f"projects/{project_id}/locations/{location}/glossaries/{glossary_id}"
    
    # Check if glossary already exists and delete it for an update
    try:
        glossary = client.get_glossary(name=name)
        print(f"Glossary {glossary_id} already exists on GCP. Deleting for update...")
        operation = client.delete_glossary(name=name)
        operation.result(timeout=180)
        print(f"Glossary {glossary_id} deleted.")
    except Exception as e:
        print(f"Glossary {glossary_id} not found or error checking: {e}")

    glossary = translate.Glossary(
        name=name,
        language_pair=translate.Glossary.LanguageCodePair(
            source_language_code="en", 
            target_language_code=target_language
        ),
        input_config=translate.GlossaryInputConfig(
            gcs_source=translate.GcsSource(input_uri=gcs_path)
        )
    )

    print(f"Registering Google Cloud Glossary: {glossary_id}...")
    # Long running operation
    operation = client.create_glossary(parent=f"projects/{project_id}/locations/{location}", glossary=glossary)
    result = operation.result(timeout=180)
    print(f"Glossary created successfully: {result.name}")
    
    return glossary_id

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        create_cloud_glossary(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python glossary_manager.py <csv_path> <target_language_code>")
