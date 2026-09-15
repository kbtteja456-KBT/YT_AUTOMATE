import sys, os, asyncio
sys.path.insert(0, r"c:\Users\DELL\OneDrive\Desktop\yt")
from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider

async def test_tokens():
    db = SyncMongoDB.get_db()
    channels = list(db.youtube_channels.find({"is_active": True}))
    print(f"Testing tokens for {len(channels)} active channels...\n")
    
    for ch in channels:
        ch_id = ch.get("channel_id")
        title = ch.get("title")
        ws_id = ch.get("workspace_id")
        print(f"Checking Channel '{title}' ({ch_id}), Workspace: {ws_id}")
        
        token_doc = db.oauth_tokens.find_one({"workspace_id": ws_id}) or db.oauth_tokens.find_one({"channel_id": ch_id})
        if not token_doc:
            print("  ❌ No token document found in DB!")
            continue
            
        encrypted_rt = token_doc.get("encrypted_refresh_token") or token_doc.get("refresh_token")
        if not encrypted_rt:
            print("  ❌ No refresh token found!")
            continue
            
        try:
            refresh_token = decrypt_token(encrypted_rt)
            print("  -> Decrypted refresh token successfully.")
            token_resp = await GoogleOAuthManager.refresh_access_token(refresh_token)
            access_token = token_resp.get("access_token")
            print(f"  -> Refreshed access token successfully! (Expires in: {token_resp.get('expires_in')}s)")
            
            creds = GoogleOAuthManager.get_google_credentials(access_token, refresh_token)
            yt_provider = YouTubeClientProvider(credentials=creds)
            service = yt_provider._get_service()
            req = service.channels().list(part="snippet,statistics", mine=True)
            res = req.execute()
            items = res.get("items", [])
            if items:
                info = items[0]["snippet"]
                print(f"  ✅ Authenticated with YouTube as: '{info.get('title')}' (ID: {items[0]['id']})")
            else:
                print("  ⚠️ YouTube authenticated, but no channel found.")
        except Exception as e:
            print(f"  ❌ Failed to refresh/authenticate: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_tokens())
