# 🎥 Facebook Video API - สรุปการทำงาน

## ✅ สิ่งที่ได้เพิ่มเข้ามา

### 1. **API Endpoint ใหม่ 2 ตัว**

#### A. `/api/facebook-graph-insights` (แนะนำ ⭐)

- ดึงข้อมูล Facebook Ads โดยตรงจาก Graph API v24.0
- รองรับการดึง video thumbnails และ URLs พร้อมกัน
- เร็วกว่าและมี features มากกว่า SDK เดิม

**Parameters:**

```
level=ad               # ad, adset, campaign
date_preset=today      # today, yesterday, last_7d, last_30d
include_videos=true    # ดึงข้อมูลวิดีโอด้วย
action_breakdowns=action_type
limit=100              # จำนวนผลลัพธ์
```

**ตัวอย่างการใช้:**

```bash
# ดึงโฆษณาวันนี้พร้อมวิดีโอ
GET /api/facebook-graph-insights?level=ad&date_preset=today&include_videos=true

# ดึงข้อมูล 7 วันล่าสุด
GET /api/facebook-graph-insights?date_preset=last_7d&limit=50
```

#### B. `/api/facebook-videos`

- เน้นเฉพาะข้อมูลวิดีโอ
- มี download URLs, embed codes, permalinks
- เหมาะสำหรับ video gallery

**Parameters:**

```
ad_id=xxx              # ระบุ Ad ID เฉพาะ (optional)
date_preset=last_7d    # ช่วงเวลา
limit=50               # จำนวนวิดีโอ
```

---

## 🔧 Configuration

เพิ่มใน `.env` file:

```env
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBPzNxxSUntCZCTVHyl5AkAZBIiwCmDzrWKMLU4VEHJxRve7oqUDSaMs8om9pdVWFLzUdeTbTvkGPuTeuQ4KvGFizMy3VsSid8vgmjZB8OMoLySRmXxyAUpAwyyhSqOO8tSZAU6IYpxarsXBbZCDzFdy8u279HxSXtyWMpIolRtjJEWLdmfU5SwZCsP
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166
FACEBOOK_APP_ID=1086145253509335
```

---

## 📊 Response Format

### Graph Insights Response:

```json
{
  "success": true,
  "api_version": "v24.0",
  "level": "ad",
  "date_preset": "today",
  "data": [
    {
      "ad_id": "120232539320390180",
      "ad_name": "MOF_A8_Sub brow lift(หมอเตชิณ)-05",
      "campaign_name": "TOF_EYE_T3*",
      "spend": "47.84",
      "impressions": "588",
      "clicks": "2",
      "ctr": "0.340136",
      "has_video": true,
      "video_thumbnail": "https://scontent.xx.fbcdn.net/...",
      "video_url": "https://video.xx.fbcdn.net/...",
      "video_permalink": "https://www.facebook.com/..."
    }
  ],
  "total_records": 53,
  "timestamp": "2025-11-19T13:00:00"
}
```

---

## 🚀 การใช้งาน

### Python Example:

```python
import requests

# Get today's ads with videos
response = requests.get(
    'http://localhost:5000/api/facebook-graph-insights',
    params={
        'level': 'ad',
        'date_preset': 'today',
        'include_videos': 'true'
    }
)

data = response.json()

# Filter ads with videos
ads_with_videos = [ad for ad in data['data'] if ad['has_video']]

for ad in ads_with_videos:
    print(f"Ad: {ad['ad_name']}")
    print(f"Video: {ad['video_permalink']}")
    print(f"Thumbnail: {ad['video_thumbnail']}")
```

### JavaScript/React Example:

```javascript
// Fetch videos
fetch("/api/facebook-graph-insights?date_preset=today&include_videos=true")
  .then((res) => res.json())
  .then((data) => {
    const videosAds = data.data.filter((ad) => ad.has_video);

    videosAds.forEach((ad) => {
      console.log(`${ad.ad_name}: ${ad.video_permalink}`);
    });
  });
```

---

## 📁 ไฟล์ที่เพิ่มเข้ามา

1. **`FACEBOOK_VIDEO_API_GUIDE.md`** - คู่มือการใช้งานแบบละเอียด
2. **`test_facebook_graph.py`** - Script ทดสอบ API ทั้งหมด
3. **`example_facebook_videos.py`** - ตัวอย่างการใช้งานจริง (5 examples)
4. **`FACEBOOK_VIDEO_QUICK_START.md`** - Quick start guide (ไฟล์นี้)

---

## 🧪 การทดสอบ

### วิธีที่ 1: Run Test Script

```bash
python test_facebook_graph.py
```

### วิธีที่ 2: Run Examples

```bash
python example_facebook_videos.py
```

### วิธีที่ 3: Manual Test

```bash
# Test basic endpoint
curl "http://localhost:5000/api/facebook-graph-insights?date_preset=today"

# Test with videos
curl "http://localhost:5000/api/facebook-graph-insights?date_preset=today&include_videos=true"

# Test video endpoint
curl "http://localhost:5000/api/facebook-videos?date_preset=last_7d"
```

---

## 🎯 Use Cases

### 1. Video Gallery

```python
# Get all videos from last 7 days
response = requests.get('/api/facebook-videos?date_preset=last_7d')
videos = response.json()['videos']

# Display in gallery
for video in videos:
    print(f"<img src='{video['thumbnail_url']}' />")
    print(f"<a href='{video['video_permalink']}'>Watch</a>")
```

### 2. Performance Dashboard

```python
# Get ads performance with videos
response = requests.get('/api/facebook-graph-insights', params={
    'date_preset': 'today',
    'include_videos': 'true',
    'action_breakdowns': 'action_type'
})

# Analyze
for ad in response.json()['data']:
    if ad['has_video']:
        print(f"{ad['ad_name']}: {ad['spend']} THB, {ad['clicks']} clicks")
```

### 3. Bulk Download

```python
# Generate download script for all videos
response = requests.get('/api/facebook-graph-insights', params={
    'date_preset': 'last_30d',
    'include_videos': 'true'
})

for ad in response.json()['data']:
    if ad.get('video_url'):
        print(f"wget -O {ad['ad_id']}.mp4 '{ad['video_url']}'")
```

---

## 📋 Comparison: Old vs New API

| Feature       | Old API (`/api/facebook-ads-campaigns`) | New API (`/api/facebook-graph-insights`) |
| ------------- | --------------------------------------- | ---------------------------------------- |
| Method        | Facebook SDK                            | Direct Graph API                         |
| Video Support | ❌ No                                   | ✅ Yes (with `include_videos=true`)      |
| Speed         | Slower                                  | Faster                                   |
| API Version   | Multiple                                | v24.0                                    |
| Caching       | 5 min                                   | No (fresh data)                          |
| Video URLs    | ❌                                      | ✅                                       |
| Thumbnails    | ❌                                      | ✅                                       |
| Embed Codes   | ❌                                      | ✅ (in `/api/facebook-videos`)           |

---

## ⚠️ Important Notes

1. **Access Token**: Token จะหมดอายุ ควรใช้ long-lived token
2. **Rate Limits**: Facebook มี rate limits ไม่ควรเรียก API บ่อยเกินไป
3. **Security**: ห้าม commit access token เข้า Git
4. **Video URLs**: บาง URLs อาจต้องการ authentication

---

## 🔗 Links

- **Full Guide**: `FACEBOOK_VIDEO_API_GUIDE.md`
- **Test Script**: `test_facebook_graph.py`
- **Examples**: `example_facebook_videos.py`
- **Main API**: `app.py`

---

## 💡 Tips

1. ใช้ `include_videos=true` เมื่อต้องการข้อมูลวิดีโอ
2. ใช้ `date_preset=today` เพื่อข้อมูลล่าสุด
3. จำกัด `limit` ถ้าต้องการข้อมูลเร็ว
4. ใช้ `video_permalink` เพื่อให้ user ดูวิดีโอ
5. ใช้ `video_thumbnail` เพื่อแสดง preview

---

## 📞 Support

หากมีปัญหาหรือต้องการความช่วยเหลือ:

1. ตรวจสอบ logs ที่ Flask console
2. ทดสอบด้วย test script
3. ดู examples ใน `example_facebook_videos.py`
