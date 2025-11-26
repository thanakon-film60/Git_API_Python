"""
Test script for Facebook Graph API endpoint
"""

import requests
import json
from datetime import datetime

# API base URL (change this to your deployed URL)
BASE_URL = "http://localhost:5000"  # or your Railway/production URL

def test_graph_insights_basic():
    """Test basic Graph API insights call"""
    print("\n" + "="*60)
    print("TEST 1: Basic Graph API Insights (Today)")
    print("="*60)
    
    url = f"{BASE_URL}/api/facebook-graph-insights"
    params = {
        'level': 'ad',
        'date_preset': 'today'
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Success: {data.get('success')}")
        print(f"📊 Total Ads: {data.get('total_records')}")
        
        if data.get('data'):
            first_ad = data['data'][0]
            print(f"\n📋 Sample Ad:")
            print(f"  - Ad ID: {first_ad.get('ad_id')}")
            print(f"  - Ad Name: {first_ad.get('ad_name')}")
            print(f"  - Campaign: {first_ad.get('campaign_name')}")
            print(f"  - Spend: {first_ad.get('spend')}")
            print(f"  - Impressions: {first_ad.get('impressions')}")
            print(f"  - Clicks: {first_ad.get('clicks')}")
    else:
        print(f"❌ Error: {response.text}")


def test_graph_insights_with_videos():
    """Test Graph API insights with video data"""
    print("\n" + "="*60)
    print("TEST 2: Graph API Insights with Videos")
    print("="*60)
    
    url = f"{BASE_URL}/api/facebook-graph-insights"
    params = {
        'level': 'ad',
        'date_preset': 'today',
        'include_videos': 'true',
        'limit': 10
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Success: {data.get('success')}")
        print(f"📊 Total Ads: {data.get('total_records')}")
        
        # Count ads with videos
        ads_with_videos = [ad for ad in data.get('data', []) if ad.get('has_video')]
        print(f"🎥 Ads with Videos: {len(ads_with_videos)}")
        
        if ads_with_videos:
            first_video_ad = ads_with_videos[0]
            print(f"\n📹 Sample Video Ad:")
            print(f"  - Ad Name: {first_video_ad.get('ad_name')}")
            print(f"  - Thumbnail: {first_video_ad.get('video_thumbnail')[:50]}..." if first_video_ad.get('video_thumbnail') else "  - Thumbnail: None")
            print(f"  - Video URL: {first_video_ad.get('video_url')[:50]}..." if first_video_ad.get('video_url') else "  - Video URL: None")
    else:
        print(f"❌ Error: {response.text}")


def test_graph_insights_with_actions():
    """Test Graph API insights with action breakdowns"""
    print("\n" + "="*60)
    print("TEST 3: Graph API Insights with Action Breakdowns")
    print("="*60)
    
    url = f"{BASE_URL}/api/facebook-graph-insights"
    params = {
        'level': 'ad',
        'date_preset': 'today',
        'action_breakdowns': 'action_type'
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Success: {data.get('success')}")
        print(f"📊 Total Ads: {data.get('total_records')}")
        
        if data.get('data'):
            first_ad = data['data'][0]
            print(f"\n📋 Sample Ad with Actions:")
            print(f"  - Ad Name: {first_ad.get('ad_name')}")
            
            actions = first_ad.get('actions', [])
            if actions:
                print(f"  - Actions ({len(actions)}):")
                for action in actions[:5]:  # Show first 5 actions
                    print(f"    • {action.get('action_type')}: {action.get('value')}")
    else:
        print(f"❌ Error: {response.text}")


def test_compare_apis():
    """Compare old API vs new Graph API"""
    print("\n" + "="*60)
    print("TEST 4: Compare APIs - SDK vs Graph API")
    print("="*60)
    
    # Test old API
    print("\n📊 Testing OLD API (Facebook SDK):")
    old_url = f"{BASE_URL}/api/facebook-ads-campaigns"
    old_params = {
        'level': 'ad',
        'date_preset': 'today',
        'limit': 10
    }
    
    old_response = requests.get(old_url, params=old_params)
    if old_response.ok:
        old_data = old_response.json()
        print(f"  ✅ Old API: {old_data.get('total_records')} records")
    else:
        print(f"  ❌ Old API failed: {old_response.status_code}")
    
    # Test new API
    print("\n📊 Testing NEW API (Graph API):")
    new_url = f"{BASE_URL}/api/facebook-graph-insights"
    new_params = {
        'level': 'ad',
        'date_preset': 'today',
        'limit': 10
    }
    
    new_response = requests.get(new_url, params=new_params)
    if new_response.ok:
        new_data = new_response.json()
        print(f"  ✅ New API: {new_data.get('total_records')} records")
    else:
        print(f"  ❌ New API failed: {new_response.status_code}")


def test_video_endpoint():
    """Test dedicated video endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Dedicated Video Endpoint")
    print("="*60)
    
    url = f"{BASE_URL}/api/facebook-videos"
    params = {
        'date_preset': 'last_7d',
        'limit': 5
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"✅ Success: {data.get('success')}")
        print(f"🎥 Total Videos: {data.get('total_videos')}")
        
        if data.get('videos'):
            first_video = data['videos'][0]
            print(f"\n📹 Sample Video:")
            print(f"  - Ad Name: {first_video.get('ad_name')}")
            print(f"  - Video Title: {first_video.get('video_title')}")
            print(f"  - Duration: {first_video.get('video_length')}s")
            print(f"  - Permalink: {first_video.get('video_permalink')}")
    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║      Facebook Graph API - Test Suite                         ║
║      Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run all tests
        test_graph_insights_basic()
        test_graph_insights_with_videos()
        test_graph_insights_with_actions()
        test_compare_apis()
        test_video_endpoint()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
