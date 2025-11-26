"""
ตรวจสอบ Token ว่ามีสิทธิ์อะไรบ้าง และเป็น Token ประเภทไหน
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_token_info(token, token_name):
    """ตรวจสอบข้อมูล Token"""
    print(f"\n{'='*60}")
    print(f"🔍 ตรวจสอบ: {token_name}")
    print(f"{'='*60}")
    
    # Debug Token endpoint
    url = "https://graph.facebook.com/v24.0/debug_token"
    params = {
        'input_token': token,
        'access_token': token  # Use same token to debug itself
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.ok and 'data' in data:
            token_data = data['data']
            
            print(f"✅ Token Type: {token_data.get('type', 'unknown')}")
            print(f"📱 App ID: {token_data.get('app_id')}")
            print(f"👤 User ID: {token_data.get('user_id')}")
            print(f"⏰ Expires: {token_data.get('expires_at', 'Never')}")
            print(f"🔓 Valid: {token_data.get('is_valid', False)}")
            
            # Check permissions
            scopes = token_data.get('scopes', [])
            print(f"\n📋 Permissions ({len(scopes)}):")
            for scope in sorted(scopes):
                print(f"   • {scope}")
            
            # Check for required permissions
            required = ['pages_read_engagement', 'pages_show_list', 'pages_read_user_content']
            missing = [p for p in required if p not in scopes]
            
            if missing:
                print(f"\n⚠️ Missing Required Permissions:")
                for perm in missing:
                    print(f"   ❌ {perm}")
            else:
                print(f"\n✅ All required permissions present!")
            
        else:
            error = data.get('error', {})
            print(f"❌ Error: {error.get('message', 'Unknown error')}")
            print(f"   Code: {error.get('code', 'N/A')}")
            print(f"   Type: {error.get('type', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

# Check both tokens
access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')

if access_token:
    check_token_info(access_token, "FACEBOOK_ACCESS_TOKEN")
else:
    print("❌ FACEBOOK_ACCESS_TOKEN not found in .env")

if page_token and page_token != access_token:
    check_token_info(page_token, "FACEBOOK_PAGE_ACCESS_TOKEN")
elif page_token == access_token:
    print("\n⚠️ FACEBOOK_PAGE_ACCESS_TOKEN is identical to FACEBOOK_ACCESS_TOKEN")
    print("   You need to generate a separate Page Access Token!")
else:
    print("\n❌ FACEBOOK_PAGE_ACCESS_TOKEN not found in .env")

print(f"\n{'='*60}")
print("💡 How to get a Page Access Token:")
print("   1. Go to: https://developers.facebook.com/tools/explorer")
print("   2. Select your app")
print("   3. Get User Access Token with pages permissions")
print("   4. Call: GET /{page_id}?fields=access_token")
print(f"{'='*60}\n")
