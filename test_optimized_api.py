"""
Test script for optimized Facebook Ads API
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_facebook_ads_basic():
    """Test basic Facebook Ads API call"""
    print("=" * 70)
    print("Test 1: Basic Facebook Ads API (today)")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/facebook-ads-campaigns"
    params = {
        'level': 'campaign',
        'date_preset': 'today'
    }
    
    start_time = time.time()
    response = requests.get(url, params=params)
    elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    print(f"Response Size: {len(response.content)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Cached: {data.get('cached')}")
        print(f"Total Records: {data.get('total_records')}")
        print(f"Summary: {json.dumps(data.get('summary'), indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    print()
    return response


def test_facebook_ads_30days():
    """Test Facebook Ads API with 30 days range and daily breakdown"""
    print("=" * 70)
    print("Test 2: Facebook Ads API (30 days with daily breakdown)")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/facebook-ads-campaigns"
    params = {
        'level': 'campaign',
        'time_range': json.dumps({
            "since": "2025-10-18",
            "until": "2025-11-17"
        }),
        'time_increment': '1'
    }
    
    start_time = time.time()
    response = requests.get(url, params=params)
    elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    print(f"Response Size: {len(response.content)} bytes")
    print(f"Response Size (KB): {len(response.content) / 1024:.2f} KB")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Cached: {data.get('cached')}")
        print(f"Total Records: {data.get('total_records')}")
        print(f"Summary: {json.dumps(data.get('summary'), indent=2)}")
        
        # Show first record as sample
        if data.get('data') and len(data['data']) > 0:
            print("\nSample Record (first):")
            sample = data['data'][0]
            print(f"  Campaign: {sample.get('campaign_name')}")
            print(f"  Date: {sample.get('date_start')} - {sample.get('date_stop')}")
            print(f"  Spend: {sample.get('spend')}")
            print(f"  Clicks: {sample.get('clicks')}")
            print(f"  Impressions: {sample.get('impressions')}")
    else:
        print(f"Error: {response.text}")
    
    print()
    return response


def test_facebook_ads_cached():
    """Test cached response"""
    print("=" * 70)
    print("Test 3: Facebook Ads API (should be cached)")
    print("=" * 70)
    
    url = f"{BASE_URL}/api/facebook-ads-campaigns"
    params = {
        'level': 'campaign',
        'time_range': json.dumps({
            "since": "2025-10-18",
            "until": "2025-11-17"
        }),
        'time_increment': '1'
    }
    
    start_time = time.time()
    response = requests.get(url, params=params)
    elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    print(f"Response Size: {len(response.content)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"✅ Cached: {data.get('cached')}")
        print(f"Cache Expires In: {data.get('cache_expires_in')}s")
        print(f"Total Records: {data.get('total_records')}")
    else:
        print(f"Error: {response.text}")
    
    print()
    return response


def test_health_check():
    """Test health check endpoint"""
    print("=" * 70)
    print("Test 4: Health Check")
    print("=" * 70)
    
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Cache Status:")
        print(json.dumps(data.get('cache_status'), indent=2))
    else:
        print(f"Error: {response.text}")
    
    print()


if __name__ == "__main__":
    print("\n🚀 Testing Optimized Facebook Ads API\n")
    
    try:
        # Test 1: Basic call
        test_facebook_ads_basic()
        
        # Wait a bit
        time.sleep(1)
        
        # Test 2: 30 days with daily breakdown (first call - not cached)
        test_facebook_ads_30days()
        
        # Test 3: Same call (should be cached and much faster)
        test_facebook_ads_cached()
        
        # Test 4: Health check
        test_health_check()
        
        print("=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("Please make sure the API server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")
