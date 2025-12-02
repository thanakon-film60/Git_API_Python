"""
Test Facebook Ads Insights API
"""
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# ใช้ Token ใหม่ที่ให้มา (Token จากคำถาม)
access_token = 'EAAPb1ZBYCiNcBPzNxxSUntCZCTVHyl5AkAZBIiwCmDzrWKMLU4VEHJxRve7oqUDSaMs8om9pdVWFLzUdeTbTvkGPuTeuQ4KvGFizMy3VsSid8vgmjZB8OMoLySRmXxyAUpAwyyhSqOO8tSZAU6IYpxarsXBbZCDzFdy8u279HxSXtyWMpIolRtjJEWLdmfU5SwZCsP5'
ad_account_id = 'act_1447972642723860'

print('=' * 60)
print('Testing Facebook Ads Insights API')
print('=' * 60)
print(f'Ad Account: {ad_account_id}')
print()

# Build API URL
url = f'https://graph.facebook.com/v24.0/{ad_account_id}/insights'
params = {
    'level': 'ad',
    'fields': 'ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc,cpm',
    'date_preset': 'yesterday',
    'access_token': access_token,
    'limit': 10
}

print(f'URL: {url}')
print(f'Date: yesterday')
print()

try:
    response = requests.get(url, params=params, timeout=30)
    print(f'Status: {response.status_code}')
    print()

    data = response.json()
    
    if 'error' in data:
        print('❌ Error:', data['error'].get('message', 'Unknown error'))
        print('Error Code:', data['error'].get('code', 'N/A'))
    else:
        ads = data.get('data', [])
        print(f'✅ Total Ads Found: {len(ads)}')
        print()
        
        # Calculate totals
        total_spend = 0
        total_impressions = 0
        total_clicks = 0
        
        for ad in ads:
            total_spend += float(ad.get('spend', 0))
            total_impressions += int(ad.get('impressions', 0))
            total_clicks += int(ad.get('clicks', 0))
        
        print('📊 Summary:')
        print(f'   Total Spend: {total_spend:.2f} THB')
        print(f'   Total Impressions: {total_impressions:,}')
        print(f'   Total Clicks: {total_clicks:,}')
        print()
        
        print('📋 Ads Detail (Top 5):')
        print('-' * 60)
        for i, ad in enumerate(ads[:5], 1):
            print(f'{i}. {ad.get("ad_name", "N/A")}')
            print(f'   Campaign: {ad.get("campaign_name", "N/A")}')
            print(f'   Spend: {ad.get("spend", "0")} THB | Impressions: {ad.get("impressions", "0")} | Clicks: {ad.get("clicks", "0")}')
            print(f'   CTR: {ad.get("ctr", "0")}% | CPC: {ad.get("cpc", "0")} | CPM: {ad.get("cpm", "0")}')
            print()

except requests.exceptions.Timeout:
    print('❌ Request timeout')
except requests.exceptions.RequestException as e:
    print(f'❌ Request error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')

print('=' * 60)
print('Test completed!')
