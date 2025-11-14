"""Test environment variables loading"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check Facebook credentials
token = os.getenv('FACEBOOK_ACCESS_TOKEN')
account_id = os.getenv('FACEBOOK_AD_ACCOUNT_ID')

print("="*70)
print("Environment Variables Test")
print("="*70)

if token:
    print(f"✅ FACEBOOK_ACCESS_TOKEN: {token[:30]}...")
else:
    print("❌ FACEBOOK_ACCESS_TOKEN: NOT FOUND")

if account_id:
    print(f"✅ FACEBOOK_AD_ACCOUNT_ID: {account_id}")
else:
    print("❌ FACEBOOK_AD_ACCOUNT_ID: NOT FOUND")

print("="*70)

# Test if credentials are set properly
if token and account_id:
    print("\n🎉 All Facebook credentials are set correctly!")
    print("\nYou can now run the API server:")
    print("  python app.py")
    print("\nThen test the endpoint:")
    print("  http://localhost:5000/api/facebook-ads-campaigns?level=campaign&date_preset=today")
else:
    print("\n❌ Missing credentials. Please check your .env file.")
