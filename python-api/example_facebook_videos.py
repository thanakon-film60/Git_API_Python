"""
Example: How to use Facebook Graph API endpoint
"""

import requests
import json

# Your API URL
API_URL = "http://localhost:5000"  # Change to your production URL

def example_1_get_today_ads_with_videos():
    """Example 1: Get today's ads with video thumbnails"""
    print("\n" + "="*60)
    print("Example 1: Get today's ads with videos")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-graph-insights", params={
        'level': 'ad',
        'date_preset': 'today',
        'include_videos': 'true'
    })
    
    if response.ok:
        data = response.json()
        
        print(f"Total ads found: {data['total_records']}")
        
        # Filter ads with videos
        ads_with_videos = [ad for ad in data['data'] if ad.get('has_video')]
        
        print(f"Ads with videos: {len(ads_with_videos)}")
        
        for ad in ads_with_videos[:3]:  # Show first 3
            print(f"\n📹 {ad['ad_name']}")
            print(f"   Campaign: {ad['campaign_name']}")
            print(f"   Spend: ${ad.get('spend', 0)}")
            print(f"   Impressions: {ad.get('impressions', 0)}")
            print(f"   Video Thumbnail: {ad.get('video_thumbnail', 'N/A')[:50]}...")
            
            if ad.get('video_permalink'):
                print(f"   📺 Watch: {ad['video_permalink']}")


def example_2_download_video_urls():
    """Example 2: Get direct video download URLs"""
    print("\n" + "="*60)
    print("Example 2: Get video download URLs")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-videos", params={
        'date_preset': 'last_7d',
        'limit': 5
    })
    
    if response.ok:
        data = response.json()
        
        print(f"Total videos: {data['total_videos']}")
        
        for video in data['videos']:
            print(f"\n🎥 {video['ad_name']}")
            print(f"   Duration: {video.get('video_length', 0)}s")
            
            if video.get('video_url'):
                print(f"   Download URL: {video['video_url'][:60]}...")
            
            if video.get('video_permalink'):
                print(f"   Public URL: {video['video_permalink']}")


def example_3_get_performance_with_actions():
    """Example 3: Get ad performance with action breakdowns"""
    print("\n" + "="*60)
    print("Example 3: Ad performance with actions")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-graph-insights", params={
        'level': 'ad',
        'date_preset': 'today',
        'action_breakdowns': 'action_type'
    })
    
    if response.ok:
        data = response.json()
        
        for ad in data['data'][:3]:  # Show first 3
            print(f"\n📊 {ad['ad_name']}")
            print(f"   Spend: ${ad.get('spend', 0)}")
            print(f"   Clicks: {ad.get('clicks', 0)}")
            print(f"   CTR: {ad.get('ctr', 0)}%")
            
            actions = ad.get('actions', [])
            if actions:
                print(f"   Actions:")
                for action in actions[:5]:
                    print(f"      • {action['action_type']}: {action['value']}")


def example_4_embed_video_in_html():
    """Example 4: Generate HTML to embed videos"""
    print("\n" + "="*60)
    print("Example 4: Generate HTML embed code")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-videos", params={
        'date_preset': 'today',
        'limit': 1
    })
    
    if response.ok:
        data = response.json()
        
        if data['videos']:
            video = data['videos'][0]
            
            html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{video['ad_name']}</title>
</head>
<body>
    <h1>{video['ad_name']}</h1>
    <p>Campaign: {video['campaign_name']}</p>
    
    <!-- Option 1: Use embed HTML -->
    {video.get('embed_html', '')}
    
    <!-- Option 2: Use iframe with permalink -->
    <iframe 
        src="{video.get('video_permalink', '')}" 
        width="640" 
        height="360"
        frameborder="0"
        allowfullscreen>
    </iframe>
    
    <!-- Option 3: Show thumbnail with link -->
    <a href="{video.get('video_permalink', '')}">
        <img src="{video.get('thumbnail_url', '')}" alt="Video Thumbnail">
    </a>
</body>
</html>
            """
            
            print("Generated HTML:")
            print(html_template)
            
            # Save to file
            with open('video_embed_example.html', 'w', encoding='utf-8') as f:
                f.write(html_template)
            
            print("\n✅ Saved to: video_embed_example.html")


def example_5_bulk_download_videos():
    """Example 5: Prepare bulk video download"""
    print("\n" + "="*60)
    print("Example 5: Bulk video download preparation")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-graph-insights", params={
        'level': 'ad',
        'date_preset': 'last_7d',
        'include_videos': 'true',
        'limit': 50
    })
    
    if response.ok:
        data = response.json()
        
        # Get all ads with videos
        video_ads = [ad for ad in data['data'] if ad.get('has_video')]
        
        print(f"Found {len(video_ads)} ads with videos")
        
        # Create download script
        download_commands = []
        
        for i, ad in enumerate(video_ads, 1):
            if ad.get('video_permalink'):
                filename = f"video_{i}_{ad['ad_id']}.mp4"
                url = ad['video_permalink']
                
                # For wget
                download_commands.append(f"wget -O {filename} '{url}'")
        
        # Save download script
        script_content = "#!/bin/bash\n\n"
        script_content += "# Facebook Ad Videos Download Script\n"
        script_content += f"# Generated on {data['timestamp']}\n\n"
        script_content += "\n".join(download_commands)
        
        with open('download_videos.sh', 'w') as f:
            f.write(script_content)
        
        print(f"✅ Generated download script: download_videos.sh")
        print(f"   Total videos: {len(download_commands)}")
        
        # Also create a JSON file with video info
        video_info = [{
            'ad_id': ad['ad_id'],
            'ad_name': ad['ad_name'],
            'campaign_name': ad['campaign_name'],
            'video_thumbnail': ad.get('video_thumbnail'),
            'video_url': ad.get('video_url'),
            'video_permalink': ad.get('video_permalink')
        } for ad in video_ads]
        
        with open('videos_info.json', 'w', encoding='utf-8') as f:
            json.dump(video_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved video info: videos_info.json")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║      Facebook Graph API - Usage Examples                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_1_get_today_ads_with_videos()
        example_2_download_video_urls()
        example_3_get_performance_with_actions()
        example_4_embed_video_in_html()
        example_5_bulk_download_videos()
        
        print("\n" + "="*60)
        print("✅ All examples completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
