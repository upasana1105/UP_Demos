import os
import requests
from dotenv import load_dotenv

load_dotenv()

def run_french_test():
    url = "http://localhost:8002/api/translate"
    file_path = "uploads/5g-edge-computing-value-opportunity.pdf"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        data = {"target_language": "fr"}
        
        print("Sending translation request to backend for French...")
        response = requests.post(url, files=files, data=data)
        print("Response Status:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except Exception as e:
            print("Response Text:", response.text)

if __name__ == "__main__":
    run_french_test()
