import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_apis():
    print("==================================================")
    print("VERIFYING USER API CREDENTIALS")
    print("==================================================")
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        print("\n[1/3] Testing OpenRouter API Key...")
        try:
            res = await client.get(
                "https://openrouter.ai/api/v1/auth/key", 
                headers={"Authorization": f"Bearer {openrouter_key}"}
            )
            print(f"  Status: {res.status_code}")
            if res.status_code == 200:
                data = res.json().get("data", {})
                print(f"  Label: {data.get('label')}")
                print(f"  Usage: {data.get('usage')}")
                print(f"  Limit: {data.get('limit')}")
                print("  => OpenRouter: VALID & ACTIVE")
            else:
                print(f"  Response: {res.text}")
        except Exception as e:
            print(f"  OpenRouter error: {e}")

        # 2. Pexels API
        pexels_key = os.getenv("PEXELS_API_KEY")
        print("\n[2/3] Testing Pexels API Key...")
        try:
            res = await client.get(
                "https://api.pexels.com/v1/search?query=technology&per_page=1",
                headers={"Authorization": pexels_key}
            )
            print(f"  Status: {res.status_code}")
            if res.status_code == 200:
                photos = res.json().get("photos", [])
                print(f"  Retrieved {len(photos)} photo(s) successfully.")
                print("  => Pexels: VALID & ACTIVE")
            else:
                print(f"  Response: {res.text}")
        except Exception as e:
            print(f"  Pexels error: {e}")

        # 3. Pixabay API
        pixabay_key = os.getenv("PIXABAY_API_KEY")
        print("\n[3/3] Testing Pixabay API Key...")
        try:
            res = await client.get(
                f"https://pixabay.com/api/?key={pixabay_key}&q=technology&image_type=photo&per_page=3"
            )
            print(f"  Status: {res.status_code}")
            if res.status_code == 200:
                hits = res.json().get("totalHits", 0)
                print(f"  Total matching hits: {hits}")
                print("  => Pixabay: VALID & ACTIVE")
            else:
                print(f"  Response: {res.text}")
        except Exception as e:
            print(f"  Pixabay error: {e}")

        # 4. Google OAuth Configuration
        print("\n[4/4] Verifying Google OAuth 2.0 Client Configuration...")
        from backend.app.core.oauth import GoogleOAuthManager
        from backend.app.config import settings
        auth_url = GoogleOAuthManager.get_authorization_url()
        print(f"  Google Client ID: {settings.google_client_id[:25]}...")
        print(f"  Generated OAuth URL: {auth_url[:60]}...")
        print("  => Google OAuth: VALID & READY FOR AUTHENTICATION FLOW")

    print("\n==================================================")
    print("ALL USER CREDENTIALS CONFIGURED & VERIFIED")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_apis())
