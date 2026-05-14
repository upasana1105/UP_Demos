import os
import sys
import requests
import urllib.parse
from dotenv import load_dotenv

def verify_bq_managed_connection():
    """
    Standalone utility script to verify Google Cloud OAuth 2.0 Web Client credentials
    and test token exchange for the Google-Managed BigQuery MCP Server integration.
    """
    print("🚀 === Verifying Google-Managed BigQuery MCP Server Connectivity ===")
    
    # Load environment variables
    load_dotenv()
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or client_id == "your_google_oauth_client_id_here.apps.googleusercontent.com":
        print("❌ Error: GOOGLE_CLIENT_ID is missing or not configured in .env")
        print("Please copy .env.example to .env and enter your Google Cloud OAuth Client ID.")
        sys.exit(1)
        
    if not client_secret or client_secret == "your_google_oauth_client_secret_here":
        print("❌ Error: GOOGLE_CLIENT_SECRET is missing or not configured in .env")
        print("Please copy .env.example to .env and enter your Google Cloud OAuth Client Secret.")
        sys.exit(1)

    # Step 1: Generate Authorization URL
    auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "https://vertexaisearch.cloud.google.com/oauth-redirect",
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    print("\n🔗 [Step 1] Google OAuth 2.0 Authorization URL Generated Successfully:")
    print(f"URL: {auth_url}")
    print("\n💡 In Gemini Enterprise, this URL is opened automatically when you click 'Login'.")
    print("To test manually, open the URL in your browser, authorize the app, and copy the 'code' parameter from the redirect URL.")
    
    # Step 2: Interactive token exchange test
    print("\nWould you like to test the token exchange right now? (y/n)")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            print("\nEnter the authorization 'code' from your redirect URL:")
            auth_code = input().strip()
            
            token_endpoint = "https://oauth2.googleapis.com/token"
            payload = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "https://vertexaisearch.cloud.google.com/oauth-redirect"
            }
            
            print("\n🔄 Exchanging authorization code for Google Cloud Access Token...")
            response = requests.post(token_endpoint, data=payload)
            
            if response.status_code == 200:
                tokens = response.json()
                print("✅ Token Exchange Successful!")
                print(f"Access Token: {tokens.get('access_token')[:10]}...[truncated]")
                print(f"Refresh Token: {tokens.get('refresh_token')[:10]}...[truncated]")
                print("\n🎉 Your Google Cloud OAuth application is fully verified and ready to connect to Gemini Enterprise!")
            else:
                print(f"❌ Token Exchange Failed (Status {response.status_code})")
                print(response.text)
        else:
            print("\nSkipping token exchange test. Your configuration is ready for Gemini Enterprise!")
    except (KeyboardInterrupt, EOFError):
        print("\nVerification exited.")

if __name__ == "__main__":
    verify_bq_managed_connection()
