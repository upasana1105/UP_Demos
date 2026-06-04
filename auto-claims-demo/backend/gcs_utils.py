# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import datetime
from google.cloud import storage
import google.auth

_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is not None:
        return _storage_client
    
    try:
        credentials, project = google.auth.default()
        _storage_client = storage.Client(credentials=credentials, project=project)
        return _storage_client
    except Exception as e:
        print(f"GCS Auth Default Failed: {e}. Trying standard Client...")
        try:
            _storage_client = storage.Client()
            return _storage_client
        except Exception as e2:
            print(f"GCS Standard Client Init Failed: {e2}. GCS will run in Mock/Local mode.")
            return None

def upload_file_to_gcs(bucket_name: str, object_name: str, file_obj) -> bool:
    client = get_storage_client()
    if not client or not bucket_name:
        print("GCS client or bucket not configured. Skipping upload to GCS.")
        return False
    
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        # Upload from file-like object
        file_obj.seek(0)
        blob.upload_from_file(file_obj)
        print(f"Successfully uploaded {object_name} to GCS bucket {bucket_name}")
        return True
    except Exception as e:
        print(f"Failed to upload to GCS: {e}")
        return False

def generate_signed_url(bucket_name: str, object_name: str) -> str:
    # If the URL is already a full http link or local upload path, return it directly
    if object_name.startswith("http://") or object_name.startswith("https://") or object_name.startswith("uploads/"):
        return object_name
        
    client = get_storage_client()
    if not client or not bucket_name:
        # Fallback to local server path
        return f"/uploads/{object_name}"
        
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET"
        )
        return url
    except Exception as e:
        print(f"Failed to generate signed URL for {object_name}: {e}")
        return f"/uploads/{object_name}"
