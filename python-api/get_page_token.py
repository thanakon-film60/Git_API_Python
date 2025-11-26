"""
สคริปต์สำหรับดึง Page Access Token จาก User Token
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_page_access_token():
    """ดึง Page Access Token จาก User Token"""
    
    user_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    page_id = '1284307720164594'  # BJH Bangkok Page ID
    
    if not user_token:
        print("❌ FACEBOOK_ACCESS_TOKEN not found in .env")
        return
    
    print("🔄 กำลังแปลง User Token เป็น Page Access Token...")
    print(f"📄 Page ID: {page_id}")
    
    # Get Page Access Token
    url = f'https://graph.facebook.com/v24.0/{page_id}'
    params = {
        'fields': 'access_token,name,id',
        'access_token': user_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.ok and 'access_token' in data:
            page_token = data['access_token']
            page_name = data.get('name', 'Unknown')
            
            print(f"\n✅ สำเร็จ! ได้ Page Access Token แล้ว")
            print(f"📄 Page Name: {page_name}")
            print(f"🔑 Page Token: {page_token[:50]}...")
            
            print(f"\n📋 คัดลอกบรรทัดนี้ไปใส่ใน .env:")
            print(f"FACEBOOK_PAGE_ACCESS_TOKEN={page_token}")
            
            # Check permissions of page token
            print(f"\n🔍 ตรวจสอบสิทธิ์ของ Page Token...")
            debug_url = "https://graph.facebook.com/v24.0/debug_token"
            debug_params = {
                'input_token': page_token,
                'access_token': user_token
            }
            
            debug_response = requests.get(debug_url, params=debug_params, timeout=10)
            debug_data = debug_response.json()
            
            if debug_response.ok and 'data' in debug_data:
                token_info = debug_data['data']
                print(f"✅ Token Type: {token_info.get('type', 'unknown')}")
                
                scopes = token_info.get('scopes', [])
                print(f"\n📋 Permissions ({len(scopes)}):")
                for scope in sorted(scopes):
                    print(f"   • {scope}")
            
            return page_token
            
        else:
            error = data.get('error', {})
            print(f"\n❌ Error: {error.get('message', 'Unknown error')}")
            print(f"   Code: {error.get('code', 'N/A')}")
            
            if error.get('code') == 190:
                print(f"\n💡 วิธีแก้ไข:")
                print(f"   1. Token หมดอายุหรือไม่ถูกต้อง")
                print(f"   2. ไปที่ https://developers.facebook.com/tools/explorer")
                print(f"   3. สร้าง User Access Token ใหม่ที่มีสิทธิ์:")
                print(f"      - pages_show_list")
                print(f"      - pages_read_engagement")
                print(f"      - pages_read_user_content")
                print(f"      - pages_manage_posts")
            elif error.get('code') == 10:
                print(f"\n💡 วิธีแก้ไข:")
                print(f"   คุณไม่มีสิทธิ์ Admin/Editor ของ Page นี้")
                print(f"   ต้องเป็น Admin หรือ Editor ของ Page ถึงจะได้ Page Token")
            
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("🔐 Get Facebook Page Access Token")
    print("="*60)
    
    token = get_page_access_token()
    
    if token:
        print(f"\n{'='*60}")
        print("✅ เสร็จสิ้น! นำ Token ด้านบนไปใส่ใน .env แล้วรีสตาร์ท Flask")
        print("="*60)
    else:
        print(f"\n{'='*60}")
        print("❌ ไม่สามารถดึง Page Token ได้")
        print("="*60)
