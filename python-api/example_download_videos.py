"""
Example: Download Facebook Ad Videos
ตัวอย่างการดาวน์โหลดวิดีโอจาก Facebook Ads
"""

import requests
import os
from datetime import datetime

API_URL = "http://localhost:5000"  # เปลี่ยนเป็น production URL ของคุณ

def download_video_from_url(video_url, filename, access_token=None):
    """ดาวน์โหลดวิดีโอจาก URL"""
    try:
        # เพิ่ม access_token ถ้าจำเป็น
        if access_token and '?' not in video_url:
            video_url = f"{video_url}?access_token={access_token}"
        
        print(f"📥 Downloading: {filename}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {filename}: {str(e)}")
        return False


def example_1_get_videos_today():
    """ตัวอย่าง 1: ดึงวิดีโอวันนี้"""
    print("\n" + "="*60)
    print("Example 1: Get Today's Videos")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-videos-direct", params={
        'date_preset': 'today'
    })
    
    if response.ok:
        data = response.json()
        videos = data.get('videos', [])
        
        print(f"\n🎥 Found {len(videos)} videos today")
        
        for video in videos:
            print(f"\n📹 {video['ad_name']}")
            print(f"   Campaign: {video['campaign_name']}")
            print(f"   Duration: {video['video_length']}s")
            print(f"   Video URL: {video['video_source_url'][:60]}...")
            print(f"   Public Link: {video['video_permalink']}")
            print(f"   Spend: ${video['ad_performance']['spend']}")
    else:
        print(f"❌ Error: {response.text}")


def example_2_download_all_videos():
    """ตัวอย่าง 2: ดาวน์โหลดวิดีโอทั้งหมดวันนี้"""
    print("\n" + "="*60)
    print("Example 2: Download All Videos")
    print("="*60)
    
    # สร้างโฟลเดอร์สำหรับเก็บวิดีโอ
    output_dir = "facebook_videos"
    os.makedirs(output_dir, exist_ok=True)
    
    # ดึงข้อมูลวิดีโอ
    response = requests.get(f"{API_URL}/api/facebook-videos-direct", params={
        'date_preset': 'today',
        'limit': 10
    })
    
    if not response.ok:
        print(f"❌ Error: {response.text}")
        return
    
    data = response.json()
    videos = data.get('videos', [])
    
    print(f"\n🎥 Found {len(videos)} videos to download")
    
    # ดาวน์โหลดแต่ละวิดีโอ
    success_count = 0
    for i, video in enumerate(videos, 1):
        # สร้างชื่อไฟล์
        filename = f"{output_dir}/video_{i}_{video['ad_id']}.mp4"
        
        # ใช้ video_source_url สำหรับดาวน์โหลด
        video_url = video['video_source_url']
        
        if video_url:
            # Note: อาจต้องเพิ่ม access_token ในบางกรณี
            if download_video_from_url(video_url, filename):
                success_count += 1
        else:
            print(f"⚠️ No source URL for video: {video['ad_name']}")
    
    print(f"\n✅ Downloaded {success_count}/{len(videos)} videos")
    print(f"📁 Saved to: {output_dir}/")


def example_3_download_specific_ad():
    """ตัวอย่าง 3: ดาวน์โหลดวิดีโอจาก Ad ID เฉพาะ"""
    print("\n" + "="*60)
    print("Example 3: Download Specific Ad Video")
    print("="*60)
    
    # ระบุ Ad ID ที่ต้องการ
    ad_id = "120232539320390180"  # เปลี่ยนเป็น Ad ID ของคุณ
    
    response = requests.get(f"{API_URL}/api/facebook-videos-direct", params={
        'ad_id': ad_id
    })
    
    if response.ok:
        data = response.json()
        videos = data.get('videos', [])
        
        if videos:
            video = videos[0]
            print(f"\n📹 Found video: {video['ad_name']}")
            
            filename = f"video_{ad_id}.mp4"
            video_url = video['video_source_url']
            
            if video_url:
                download_video_from_url(video_url, filename)
            else:
                print(f"⚠️ No source URL available")
        else:
            print(f"❌ No video found for Ad ID: {ad_id}")
    else:
        print(f"❌ Error: {response.text}")


def example_4_create_video_gallery_html():
    """ตัวอย่าง 4: สร้าง HTML gallery"""
    print("\n" + "="*60)
    print("Example 4: Create HTML Video Gallery")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-videos-direct", params={
        'date_preset': 'today'
    })
    
    if not response.ok:
        print(f"❌ Error: {response.text}")
        return
    
    data = response.json()
    videos = data.get('videos', [])
    
    # สร้าง HTML
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Facebook Ad Videos Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #1877f2;
            text-align: center;
        }
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .video-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .video-card img {
            width: 100%;
            border-radius: 4px;
            cursor: pointer;
        }
        .video-card h3 {
            margin: 10px 0;
            font-size: 16px;
        }
        .video-card p {
            color: #666;
            font-size: 14px;
            margin: 5px 0;
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background: #1877f2;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 5px 5px 0 0;
            font-size: 14px;
        }
        .btn:hover {
            background: #166fe5;
        }
        .stats {
            background: #f0f2f5;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .stats span {
            display: inline-block;
            margin-right: 15px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <h1>🎥 Facebook Ad Videos Gallery</h1>
    <p style="text-align: center; color: #666;">
        Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f"""
    </p>
    
    <div class="video-grid">
"""
    
    for video in videos:
        html_content += f"""
        <div class="video-card">
            <a href="{video['video_permalink']}" target="_blank">
                <img src="{video['thumbnail_url']}" alt="{video['video_title']}" />
            </a>
            <h3>{video['ad_name']}</h3>
            <p><strong>Campaign:</strong> {video['campaign_name']}</p>
            <p><strong>Duration:</strong> {video['video_length']}s</p>
            
            <div class="stats">
                <span>💰 ${video['ad_performance']['spend']}</span>
                <span>👁️ {video['ad_performance']['impressions']}</span>
                <span>👆 {video['ad_performance']['clicks']}</span>
            </div>
            
            <div style="margin-top: 10px;">
                <a href="{video['video_permalink']}" target="_blank" class="btn">
                    ▶️ Watch
                </a>
                <a href="{video['video_source_url']}" download class="btn">
                    ⬇️ Download
                </a>
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # บันทึกเป็นไฟล์
    with open('video_gallery.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created HTML gallery: video_gallery.html")
    print(f"   Total videos: {len(videos)}")
    print(f"   Open in browser to view")


def example_5_generate_download_script():
    """ตัวอย่าง 5: สร้าง bash script สำหรับดาวน์โหลด"""
    print("\n" + "="*60)
    print("Example 5: Generate Download Script")
    print("="*60)
    
    response = requests.get(f"{API_URL}/api/facebook-videos-direct", params={
        'date_preset': 'last_7d',
        'limit': 50
    })
    
    if not response.ok:
        print(f"❌ Error: {response.text}")
        return
    
    data = response.json()
    videos = data.get('videos', [])
    
    # สร้าง bash script
    script_content = "#!/bin/bash\n\n"
    script_content += "# Facebook Ad Videos Download Script\n"
    script_content += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    script_content += f"# Total videos: {len(videos)}\n\n"
    script_content += "mkdir -p facebook_videos\n"
    script_content += "cd facebook_videos\n\n"
    
    for i, video in enumerate(videos, 1):
        filename = f"video_{i}_{video['ad_id']}.mp4"
        video_url = video['video_source_url']
        
        if video_url:
            script_content += f"# {video['ad_name']}\n"
            script_content += f"echo 'Downloading {i}/{len(videos)}: {video['ad_name']}'\n"
            script_content += f"curl -L -o '{filename}' '{video_url}'\n\n"
    
    # บันทึก script
    with open('download_videos.sh', 'w') as f:
        f.write(script_content)
    
    # ทำให้ script สามารถรันได้ (สำหรับ Linux/Mac)
    os.chmod('download_videos.sh', 0o755)
    
    print(f"✅ Generated download script: download_videos.sh")
    print(f"   Total videos: {len(videos)}")
    print(f"   Run with: bash download_videos.sh")
    
    # สร้าง PowerShell script สำหรับ Windows
    ps_content = "# Facebook Ad Videos Download Script (PowerShell)\n"
    ps_content += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    ps_content += f"# Total videos: {len(videos)}\n\n"
    ps_content += "New-Item -ItemType Directory -Force -Path facebook_videos\n"
    ps_content += "Set-Location facebook_videos\n\n"
    
    for i, video in enumerate(videos, 1):
        filename = f"video_{i}_{video['ad_id']}.mp4"
        video_url = video['video_source_url']
        
        if video_url:
            ps_content += f"# {video['ad_name']}\n"
            ps_content += f"Write-Host 'Downloading {i}/{len(videos)}: {video['ad_name']}'\n"
            ps_content += f"Invoke-WebRequest -Uri '{video_url}' -OutFile '{filename}'\n\n"
    
    with open('download_videos.ps1', 'w') as f:
        f.write(ps_content)
    
    print(f"✅ Generated PowerShell script: download_videos.ps1")
    print(f"   Run with: powershell -ExecutionPolicy Bypass -File download_videos.ps1")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║      Facebook Video Download Examples                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        example_1_get_videos_today()
        example_2_download_all_videos()
        # example_3_download_specific_ad()  # Uncomment to test
        example_4_create_video_gallery_html()
        example_5_generate_download_script()
        
        print("\n" + "="*60)
        print("✅ All examples completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
