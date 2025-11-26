# 🎬 วิธีดึงและดาวน์โหลดวิดีโอจาก Facebook Ads

## ✅ API Endpoint ใหม่: `/api/facebook-videos-direct`

API นี้จะคืนค่า **video URLs ที่สามารถดาวน์โหลดได้โดยตรง**

---

## 🚀 Quick Start

### 1. ดึงวิดีโอวันนี้

```bash
GET /api/facebook-videos-direct?date_preset=today
```

### 2. ดึงวิดีโอ 7 วันล่าสุด

```bash
GET /api/facebook-videos-direct?date_preset=last_7d&limit=50
```

### 3. ดึงวิดีโอจาก Ad ID เฉพาะ

```bash
GET /api/facebook-videos-direct?ad_id=120232539320390180
```

---

## 📊 Response Format

```json
{
  "success": true,
  "date_preset": "today",
  "videos": [
    {
      "ad_id": "120232539320390180",
      "ad_name": "MOF_A8_Sub brow lift(หมอเตชิณ)-05",
      "campaign_name": "TOF_EYE_T3*",
      "video_id": "1234567890",
      "video_title": "Sub brow lift procedure",
      "video_length": 45.5,
      "video_source_url": "https://video.xx.fbcdn.net/v/xxx.mp4?...",
      "video_permalink": "https://www.facebook.com/watch/?v=xxx",
      "thumbnail_url": "https://scontent.xx.fbcdn.net/...",
      "ad_performance": {
        "spend": "47.84",
        "impressions": "588",
        "clicks": "2"
      }
    }
  ],
  "total_videos": 1
}
```

---

## 💡 วิธีใช้ video URLs

### A. ดาวน์โหลดด้วย curl/wget

```bash
# Method 1: ใช้ video_source_url โดยตรง
curl -O "https://video.xx.fbcdn.net/v/xxx.mp4?..."

# Method 2: ใช้ wget
wget "https://video.xx.fbcdn.net/v/xxx.mp4?..."

# Method 3: เพิ่ม access token ถ้าจำเป็น
curl -O "https://video.xx.fbcdn.net/v/xxx.mp4?access_token=YOUR_TOKEN"
```

### B. ดาวน์โหลดด้วย Python

```python
import requests

# ดึงข้อมูลวิดีโอ
response = requests.get('http://localhost:5000/api/facebook-videos-direct?date_preset=today')
videos = response.json()['videos']

# ดาวน์โหลดวิดีโอแรก
video = videos[0]
video_url = video['video_source_url']

# ดาวน์โหลด
response = requests.get(video_url, stream=True)
with open('video.mp4', 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"✅ Downloaded: {video['ad_name']}")
```

### C. ดาวน์โหลดด้วย PowerShell

```powershell
# ดึงข้อมูลวิดีโอ
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/facebook-videos-direct?date_preset=today"
$videos = $response.videos

# ดาวน์โหลดวิดีโอแรก
$video = $videos[0]
$videoUrl = $video.video_source_url
$filename = "video_$($video.ad_id).mp4"

Invoke-WebRequest -Uri $videoUrl -OutFile $filename
Write-Host "✅ Downloaded: $filename"
```

---

## 🎯 Use Cases

### 1. สร้าง Video Gallery

```python
# ดึงวิดีโอทั้งหมด
response = requests.get('/api/facebook-videos-direct?date_preset=last_7d')
videos = response.json()['videos']

# แสดงใน HTML
for video in videos:
    print(f"""
    <div class="video-card">
        <img src="{video['thumbnail_url']}" />
        <h3>{video['ad_name']}</h3>
        <a href="{video['video_permalink']}">Watch Video</a>
        <a href="{video['video_source_url']}" download>Download</a>
    </div>
    """)
```

### 2. Bulk Download

```python
import os
import requests

# สร้างโฟลเดอร์
os.makedirs('videos', exist_ok=True)

# ดึงวิดีโอ
response = requests.get('/api/facebook-videos-direct?date_preset=today')
videos = response.json()['videos']

# ดาวน์โหลดทั้งหมด
for i, video in enumerate(videos, 1):
    filename = f"videos/video_{i}_{video['ad_id']}.mp4"
    video_url = video['video_source_url']

    print(f"Downloading {i}/{len(videos)}: {video['ad_name']}")

    r = requests.get(video_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✅ Saved: {filename}")
```

### 3. Auto-generate Download Script

```bash
# รัน example script
python example_download_videos.py

# จะสร้างไฟล์:
# - download_videos.sh (สำหรับ Linux/Mac)
# - download_videos.ps1 (สำหรับ Windows)
# - video_gallery.html (HTML gallery)
```

---

## ⚡ สคริปต์สำเร็จรูป

### ดาวน์โหลดทุกวิดีโอวันนี้:

```bash
python example_download_videos.py
```

สคริปต์นี้จะ:

- ✅ ดึงวิดีโอวันนี้ทั้งหมด
- ✅ ดาวน์โหลดอัตโนมัติไปที่โฟลเดอร์ `facebook_videos/`
- ✅ สร้าง HTML gallery
- ✅ สร้าง download scripts

---

## 🔍 Fields ที่ได้รับ

| Field              | Type   | Description                                     |
| ------------------ | ------ | ----------------------------------------------- |
| `video_source_url` | string | **URL สำหรับดาวน์โหลดวิดีโอโดยตรง** ⭐          |
| `video_permalink`  | string | ลิงก์สาธารณะบน Facebook                         |
| `thumbnail_url`    | string | รูป thumbnail                                   |
| `video_length`     | float  | ความยาววิดีโอ (วินาที)                          |
| `ad_performance`   | object | ข้อมูล performance (spend, impressions, clicks) |

---

## ⚠️ Important Notes

1. **video_source_url** คือ URL ที่พร้อมดาวน์โหลดโดยตรง
2. บาง URLs อาจต้องเพิ่ม `?access_token=YOUR_TOKEN`
3. URLs มีอายุจำกัด (ประมาณ 24 ชั่วโมง)
4. ควรดาวน์โหลดทันที หรือ refresh API ใหม่

---

## 🆚 Comparison

| Feature             | `/api/facebook-videos-direct` ⭐ | `/api/facebook-videos` |
| ------------------- | -------------------------------- | ---------------------- |
| Direct Download URL | ✅                               | ⚠️ อาจไม่มี            |
| Thumbnail           | ✅                               | ✅                     |
| Performance Data    | ✅                               | ❌                     |
| Speed               | 🚀 Fast                          | 🐢 Slower              |
| Recommended         | ✅ Yes                           | For SDK usage          |

---

## 📞 Examples

### Example 1: ดึงวิดีโอวันนี้

```bash
curl "http://localhost:5000/api/facebook-videos-direct?date_preset=today"
```

### Example 2: ดึงวิดีโอ + ดาวน์โหลดทันที

```python
import requests

# ดึงข้อมูล
response = requests.get('http://localhost:5000/api/facebook-videos-direct?date_preset=today')
videos = response.json()['videos']

# ดาวน์โหลดวิดีโอแรก
if videos:
    video_url = videos[0]['video_source_url']
    video_response = requests.get(video_url, stream=True)

    with open('my_video.mp4', 'wb') as f:
        for chunk in video_response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("✅ Downloaded successfully!")
```

---

## 🎁 Bonus: Auto Download Script

ไฟล์ `example_download_videos.py` มีตัวอย่างพร้อมใช้งาน 5 แบบ:

1. ✅ ดึงวิดีโอวันนี้
2. ✅ ดาวน์โหลดทั้งหมดอัตโนมัติ
3. ✅ ดาวน์โหลดจาก Ad ID เฉพาะ
4. ✅ สร้าง HTML video gallery
5. ✅ สร้าง bash/PowerShell download scripts

รันเลย:

```bash
python example_download_videos.py
```

---

## ✨ Summary

**API นี้ให้:**

- ✅ Direct video download URLs
- ✅ Thumbnail images
- ✅ Ad performance data
- ✅ Public permalinks
- ✅ รองรับทุก date preset

**ใช้งานง่าย:**

```bash
# 1. เรียก API
GET /api/facebook-videos-direct?date_preset=today

# 2. ดาวน์โหลดจาก video_source_url
curl -O "{video_source_url}"

# เสร็จแล้ว! 🎉
```
