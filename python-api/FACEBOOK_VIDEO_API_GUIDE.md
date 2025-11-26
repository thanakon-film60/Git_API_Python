# Facebook Video API Guide

## 📹 Overview

API สำหรับดึงข้อมูลวิดีโอจาก Facebook Ads โดยใช้ App ID `1086145253509335`

---

## 🔧 Configuration

### Required Environment Variables

เพิ่มค่าต่อไปนี้ใน `.env` file:

```env
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBPzNxxSUntCZCTVHyl5AkAZBIiwCmDzrWKMLU4VEHJxRve7oqUDSaMs8om9pdVWFLzUdeTbTvkGPuTeuQ4KvGFizMy3VsSid8vgmjZB8OMoLySRmXxyAUpAwyyhSqOO8tSZAU6IYpxarsXBbZCDzFdy8u279HxSXtyWMpIolRtjJEWLdmfU5SwZCsP
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166
FACEBOOK_APP_ID=1086145253509335
```

> ⚠️ **Security Note**: Never commit access tokens to Git! Use environment variables or secret management tools.

---

## 📡 API Endpoints

### 1. Get Facebook Ad Insights (Direct Graph API)

**Endpoint:** `GET /api/facebook-graph-insights`

**Description:** ดึงข้อมูล insights จาก Facebook Graph API โดยตรง (พร้อม video thumbnails)

#### Query Parameters

| Parameter           | Type    | Default | Description                                            |
| ------------------- | ------- | ------- | ------------------------------------------------------ |
| `level`             | string  | `ad`    | Level ของข้อมูล (`ad`, `adset`, `campaign`)            |
| `date_preset`       | string  | `today` | ช่วงเวลา (`today`, `yesterday`, `last_7d`, `last_30d`) |
| `action_breakdowns` | string  | -       | การแยกย่อย actions (เช่น `action_type`)                |
| `include_videos`    | boolean | `false` | ดึงข้อมูลวิดีโอด้วยหรือไม่                             |
| `limit`             | integer | `100`   | จำนวนผลลัพธ์สูงสุด                                     |

### 2. Get Facebook Videos

**Endpoint:** `GET /api/facebook-videos`

**Description:** ดึงข้อมูลวิดีโอจาก Facebook Ads พร้อม download URLs

#### Query Parameters

| Parameter     | Type    | Default   | Description                                            |
| ------------- | ------- | --------- | ------------------------------------------------------ |
| `ad_id`       | string  | -         | Facebook Ad ID (ถ้าระบุจะดึงเฉพาะ ad นั้น)             |
| `level`       | string  | `ad`      | Level ของข้อมูล (`ad`, `adset`, `campaign`)            |
| `date_preset` | string  | `last_7d` | ช่วงเวลา (`today`, `yesterday`, `last_7d`, `last_30d`) |
| `limit`       | integer | `50`      | จำนวนวิดีโอสูงสุดที่จะดึง                              |

---

## 📝 Usage Examples

### Example 1: Get All Videos (Last 7 Days)

```bash
GET /api/facebook-videos
```

**Response:**

```json
{
  "success": true,
  "app_id": "1086145253509335",
  "date_range": {
    "since": "2025-11-12",
    "until": "2025-11-19"
  },
  "videos": [
    {
      "ad_id": "120232539320390180",
      "ad_name": "MOF_A8_Sub brow lift(หมอเตชิณ)-05",
      "adset_name": "G3_Broad_Thruplay",
      "campaign_name": "TOF_EYE_T3*",
      "video_id": "1234567890",
      "video_title": "Sub brow lift procedure",
      "video_description": "Video description here",
      "video_length": 45.5,
      "video_url": "https://video.xx.fbcdn.net/...",
      "video_permalink": "https://www.facebook.com/...",
      "thumbnail_url": "https://scontent.xx.fbcdn.net/...",
      "embed_html": "<iframe src='...' />",
      "created_time": "2025-11-15T10:30:00+0000",
      "updated_time": "2025-11-15T10:30:00+0000"
    }
  ],
  "total_videos": 1,
  "timestamp": "2025-11-19T11:26:16.484306",
  "usage_notes": {
    "video_url": "Direct video file URL (may require authentication)",
    "video_permalink": "Public Facebook video link",
    "embed_html": "HTML embed code for the video",
    "thumbnail_url": "Video thumbnail image URL"
  }
}
```

### Example 2: Get Video from Specific Ad

```bash
GET /api/facebook-videos?ad_id=120232539320390180
```

### Example 3: Get Videos from Last 30 Days

```bash
GET /api/facebook-videos?date_preset=last_30d&limit=100
```

---

## 🎥 Video Data Fields

| Field               | Type   | Description                                      |
| ------------------- | ------ | ------------------------------------------------ |
| `ad_id`             | string | Facebook Ad ID                                   |
| `ad_name`           | string | ชื่อโฆษณา                                        |
| `adset_name`        | string | ชื่อ Ad Set                                      |
| `campaign_name`     | string | ชื่อ Campaign                                    |
| `video_id`          | string | Facebook Video ID                                |
| `video_title`       | string | ชื่อวิดีโอ                                       |
| `video_description` | string | รายละเอียดวิดีโอ                                 |
| `video_length`      | float  | ความยาววิดีโอ (วินาที)                           |
| `video_url`         | string | URL ไฟล์วิดีโอโดยตรง (อาจต้องการ authentication) |
| `video_permalink`   | string | ลิงก์วิดีโอสาธารณะบน Facebook                    |
| `thumbnail_url`     | string | URL รูปภาพ thumbnail                             |
| `embed_html`        | string | HTML embed code สำหรับฝังวิดีโอ                  |
| `created_time`      | string | เวลาที่สร้างวิดีโอ                               |
| `updated_time`      | string | เวลาที่อัปเดตวิดีโอล่าสุด                        |

---

## 💡 Usage Notes

### 1. Video URL Types

API จะส่งค่า 3 รูปแบบสำหรับเข้าถึงวิดีโอ:

- **`video_url`**: URL ไฟล์วิดีโอโดยตรง (อาจต้องการ authentication token)
- **`video_permalink`**: ลิงก์สาธารณะบน Facebook (ใช้งานได้ทันที)
- **`embed_html`**: HTML code สำหรับฝังวิดีโอในเว็บไซต์

### 2. Using Video in Your Application

#### Option A: Use Public Link (Recommended)

```javascript
// Use video_permalink for direct Facebook video page
window.open(videoData.video_permalink);
```

#### Option B: Embed Video

```javascript
// Use embed_html to embed video in your page
const container = document.getElementById("video-container");
container.innerHTML = videoData.embed_html;
```

#### Option C: Download Video (Advanced)

```javascript
// Use video_url with access token
const videoUrl = `${videoData.video_url}?access_token=${FACEBOOK_ACCESS_TOKEN}`;
```

### 3. Display Thumbnail

```html
<img src="${videoData.thumbnail_url}" alt="${videoData.video_title}" />
```

---

## 🔐 Authentication

API ใช้ Facebook Access Token ที่ตั้งค่าใน environment variables:

- Token ต้องมีสิทธิ์ `ads_read` และ `ads_management`
- Token ต้อง active และไม่หมดอายุ
- ใช้ App ID `1086145253509335`

---

## ⚠️ Error Handling

### Common Errors

#### 1. Missing Credentials

```json
{
  "success": false,
  "error": "Missing Facebook credentials. Please set FACEBOOK_ACCESS_TOKEN and FACEBOOK_AD_ACCOUNT_ID",
  "videos": [],
  "timestamp": "2025-11-19T11:26:16.484306"
}
```

**Solution:** ตรวจสอบว่าตั้งค่า environment variables ครบถ้วน

#### 2. Invalid Ad ID

```json
{
  "success": true,
  "videos": [],
  "total_videos": 0
}
```

**Solution:** ตรวจสอบว่า Ad ID ถูกต้องและโฆษณามีวิดีโอ

#### 3. API Rate Limit

```json
{
  "success": false,
  "error": "Facebook API rate limit exceeded"
}
```

**Solution:** รอสักครู่แล้วลองใหม่ หรือลด `limit` parameter

---

## 🚀 Integration Example

### React Component Example

```jsx
import React, { useState, useEffect } from "react";

function FacebookVideos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await fetch("/api/facebook-videos?date_preset=last_7d");
      const data = await response.json();

      if (data.success) {
        setVideos(data.videos);
      }
    } catch (error) {
      console.error("Error fetching videos:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="videos-container">
      <h2>Facebook Ad Videos ({videos.length})</h2>
      {videos.map((video) => (
        <div key={video.video_id} className="video-card">
          <img
            src={video.thumbnail_url}
            alt={video.video_title}
            onClick={() => window.open(video.video_permalink)}
          />
          <h3>{video.ad_name}</h3>
          <p>Campaign: {video.campaign_name}</p>
          <p>Duration: {video.video_length}s</p>
          <a href={video.video_permalink} target="_blank">
            Watch Video
          </a>
        </div>
      ))}
    </div>
  );
}

export default FacebookVideos;
```

---

## 📊 Performance Tips

1. **Use Caching**: API มี built-in caching (5 นาที)
2. **Limit Results**: ใช้ `limit` parameter เพื่อจำกัดจำนวนผลลัพธ์
3. **Specific Ad ID**: ถ้ารู้ Ad ID ควรระบุเพื่อประหยัดเวลา
4. **Date Range**: ใช้ `date_preset` ที่เหมาะสมกับความต้องการ

---

## 🔗 Related Endpoints

- `/api/facebook-ads-campaigns` - ดึงข้อมูล campaign ทั้งหมด
- `/api/facebook-ads-manager` - Alias สำหรับ campaigns API

---

## 📞 Support

หากพบปัญหาหรือมีคำถาม กรุณาติดต่อทีม Development
