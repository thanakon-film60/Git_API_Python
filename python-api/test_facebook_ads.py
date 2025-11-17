"""
Test script for Facebook Ads Manager API
"""
import requests
import json
from datetime import datetime, timedelta

# API base URL
API_URL = "http://localhost:5000"

def test_root():
    """Test root endpoint"""
    print("=" * 60)
    print("Testing Root Endpoint")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_facebook_ads_basic():
    """Test basic Facebook Ads endpoint"""
    print("=" * 60)
    print("Testing Facebook Ads - Basic (Today)")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/facebook-ads-campaigns")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Level: {data.get('level')}")
        print(f"Date Preset: {data.get('date_preset')}")
        print(f"Total Records: {data.get('total_records')}")
        
        if 'summary' in data:
            print("\nSummary:")
            summary = data['summary']
            print(f"  Total Spend: ${summary.get('total_spend', 0):.2f}")
            print(f"  Total Impressions: {summary.get('total_impressions', 0):,}")
            print(f"  Total Clicks: {summary.get('total_clicks', 0):,}")
            print(f"  Total Conversions: {summary.get('total_conversions', 0):.2f}")
            print(f"  Average CPC: ${summary.get('average_cpc', 0):.2f}")
            print(f"  Average CTR: {summary.get('average_ctr', 0):.2f}%")
            print(f"  Cost Per Result: ${summary.get('cost_per_result', 0):.2f}")
        
        if data.get('data'):
            print(f"\nFirst campaign data:")
            print(json.dumps(data['data'][0], indent=2, default=str))
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_facebook_ads_last_7d():
    """Test Facebook Ads with last 7 days"""
    print("=" * 60)
    print("Testing Facebook Ads - Last 7 Days")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/facebook-ads-campaigns?date_preset=last_7d")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Level: {data.get('level')}")
        print(f"Date Range: {data.get('time_range')}")
        print(f"Total Records: {data.get('total_records')}")
        
        if 'summary' in data:
            print("\nSummary:")
            summary = data['summary']
            print(f"  Total Spend: ${summary.get('total_spend', 0):.2f}")
            print(f"  Total Impressions: {summary.get('total_impressions', 0):,}")
            print(f"  Total Clicks: {summary.get('total_clicks', 0):,}")
            print(f"  Total Conversions: {summary.get('total_conversions', 0):.2f}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_facebook_ads_daily():
    """Test Facebook Ads with daily breakdown"""
    print("=" * 60)
    print("Testing Facebook Ads - Daily Breakdown")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/facebook-ads-campaigns?date_preset=last_7d&time_increment=1")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Level: {data.get('level')}")
        print(f"Time Increment: {data.get('time_increment')}")
        print(f"Total Records: {data.get('total_records')}")
        
        if data.get('data'):
            print(f"\nShowing first 3 daily records:")
            for i, record in enumerate(data['data'][:3]):
                print(f"\nDay {i+1}:")
                print(f"  Date: {record.get('date_start')} to {record.get('date_stop')}")
                print(f"  Campaign: {record.get('campaign_name')}")
                print(f"  Spend: ${float(record.get('spend', 0)):.2f}")
                print(f"  Clicks: {record.get('clicks')}")
                print(f"  Conversions: {record.get('total_conversions', 0)}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_facebook_ads_adset():
    """Test Facebook Ads at adset level"""
    print("=" * 60)
    print("Testing Facebook Ads - AdSet Level")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/facebook-ads-campaigns?level=adset&date_preset=last_7d")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success!")
        print(f"Level: {data.get('level')}")
        print(f"Total Records: {data.get('total_records')}")
        
        if data.get('data'):
            print(f"\nFirst adset data:")
            first = data['data'][0]
            print(f"  Campaign: {first.get('campaign_name')}")
            print(f"  AdSet: {first.get('adset_name')}")
            print(f"  Spend: ${float(first.get('spend', 0)):.2f}")
            print(f"  Clicks: {first.get('clicks')}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def test_facebook_ads_manager_alias():
    """Test Facebook Ads Manager alias endpoint"""
    print("=" * 60)
    print("Testing Facebook Ads Manager (Alias)")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/api/facebook-ads-manager?date_preset=today")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Alias endpoint works.")
        print(f"Level: {data.get('level')}")
        print(f"Total Records: {data.get('total_records')}")
    else:
        print(f"❌ Error: {response.text}")
    print()

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Facebook Ads Manager API Test Suite")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Root endpoint
        test_root()
        
        # Test 2: Basic Facebook Ads
        test_facebook_ads_basic()
        
        # Test 3: Last 7 days
        test_facebook_ads_last_7d()
        
        # Test 4: Daily breakdown
        test_facebook_ads_daily()
        
        # Test 5: AdSet level
        test_facebook_ads_adset()
        
        # Test 6: Alias endpoint
        test_facebook_ads_manager_alias()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 60)
        print("❌ Error: Cannot connect to API")
        print("Please make sure the API is running on http://localhost:5000")
        print("Run: python app.py")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
