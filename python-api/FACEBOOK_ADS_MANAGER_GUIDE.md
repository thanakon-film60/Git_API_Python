# Facebook Ads Manager API Guide

## Overview

API สำหรับดึงข้อมูลจาก Facebook Ads Manager โดยใช้ Facebook Marketing API

## Endpoints

### 1. Get Facebook Ads Data

```
GET /api/facebook-ads-campaigns
GET /api/facebook-ads-manager (alias)
```

## Query Parameters

### Required Parameters

ไม่มี - ใช้ค่า default ได้

### Optional Parameters

| Parameter        | Type        | Default    | Description                                                                                  |
| ---------------- | ----------- | ---------- | -------------------------------------------------------------------------------------------- |
| `level`          | string      | `campaign` | ระดับของข้อมูล: `campaign`, `adset`, หรือ `ad`                                               |
| `date_preset`    | string      | `today`    | ช่วงเวลาที่กำหนดไว้: `today`, `yesterday`, `last_7d`, `last_30d`, `this_month`, `last_month` |
| `time_range`     | JSON string | -          | ช่วงเวลาแบบกำหนดเอง: `{"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}`                        |
| `time_increment` | string      | -          | การแบ่งข้อมูลตามเวลา: `1` (รายวัน), `monthly` (รายเดือน)                                     |
| `fields`         | string      | -          | ฟิลด์เพิ่มเติม (คั่นด้วย comma)                                                              |

## Example Usage

### 1. Get Campaign Data (Today)

```bash
GET /api/facebook-ads-campaigns
```

### 2. Get Campaign Data (Last 7 Days)

```bash
GET /api/facebook-ads-campaigns?date_preset=last_7d
```

### 3. Get Campaign Data (Custom Date Range)

```bash
GET /api/facebook-ads-campaigns?time_range={"since":"2025-11-01","until":"2025-11-17"}
```

### 4. Get Ad Set Level Data

```bash
GET /api/facebook-ads-campaigns?level=adset&date_preset=last_30d
```

### 5. Get Ad Level Data

```bash
GET /api/facebook-ads-campaigns?level=ad&date_preset=this_month
```

### 6. Get Daily Breakdown

```bash
GET /api/facebook-ads-campaigns?date_preset=last_7d&time_increment=1
```

### 7. Get Monthly Breakdown

```bash
GET /api/facebook-ads-campaigns?date_preset=last_month&time_increment=monthly
```

## Response Format

### Success Response

```json
{
  "success": true,
  "level": "campaign",
  "date_preset": "today",
  "time_range": {
    "since": "2025-11-17",
    "until": "2025-11-17"
  },
  "time_increment": null,
  "data": [
    {
      "campaign_id": "123456789",
      "campaign_name": "My Campaign",
      "spend": "100.50",
      "impressions": "10000",
      "clicks": "500",
      "ctr": "5.0",
      "cpc": "0.201",
      "cpm": "10.05",
      "reach": "8000",
      "frequency": "1.25",
      "actions": [
        {
          "action_type": "lead",
          "value": "25"
        },
        {
          "action_type": "purchase",
          "value": "5"
        }
      ],
      "processed_actions": {
        "lead": 25,
        "purchase": 5
      },
      "conversions": [
        {
          "action_type": "lead",
          "value": "25"
        }
      ],
      "total_conversions": 30,
      "cost_per_result": 3.35,
      "date_start": "2025-11-17",
      "date_stop": "2025-11-17"
    }
  ],
  "summary": {
    "total_spend": 100.5,
    "total_impressions": 10000,
    "total_reach": 8000,
    "total_clicks": 500,
    "total_conversions": 30,
    "total_leads": 25,
    "total_purchase": 5,
    "average_cpc": 0.2,
    "average_ctr": 5.0,
    "cost_per_result": 3.35,
    "frequency": 1.25
  },
  "total_records": 1,
  "timestamp": "2025-11-17T10:30:00"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "data": [],
  "timestamp": "2025-11-17T10:30:00"
}
```

## Available Metrics

### Default Fields

- `campaign_id` - Campaign ID
- `campaign_name` - ชื่อ Campaign
- `adset_id` - Ad Set ID (เมื่อ level=adset หรือ ad)
- `adset_name` - ชื่อ Ad Set (เมื่อ level=adset หรือ ad)
- `ad_id` - Ad ID (เมื่อ level=ad)
- `ad_name` - ชื่อ Ad (เมื่อ level=ad)
- `spend` - จำนวนเงินที่ใช้ไป
- `impressions` - จำนวน Impressions
- `clicks` - จำนวน Clicks
- `ctr` - Click-Through Rate (%)
- `cpc` - Cost Per Click
- `cpm` - Cost Per 1000 Impressions
- `cpp` - Cost Per 1000 People Reached
- `reach` - จำนวนคนที่เห็นโฆษณา
- `frequency` - ความถี่ในการเห็นโฆษณาต่อคน
- `actions` - การกระทำต่างๆ (lead, purchase, etc.)
- `conversions` - จำนวน Conversions
- `date_start` - วันที่เริ่มต้น
- `date_stop` - วันที่สิ้นสุด

### Summary Metrics

- `total_spend` - ยอดรวมค่าใช้จ่าย
- `total_impressions` - ยอดรวม Impressions
- `total_reach` - ยอดรวม Reach
- `total_clicks` - ยอดรวม Clicks
- `total_conversions` - ยอดรวม Conversions
- `total_leads` - ยอดรวม Leads
- `total_purchase` - ยอดรวม Purchases
- `average_cpc` - ค่าเฉลี่ย Cost Per Click
- `average_ctr` - ค่าเฉลี่ย CTR
- `cost_per_result` - ค่าใช้จ่ายต่อ Conversion
- `frequency` - ค่าเฉลี่ย Frequency

## Action Types

Facebook Ads API มี action types ที่หลากหลาย รวมถึง:

- `lead` - Lead generation
- `purchase` - การซื้อ
- `complete_registration` - การลงทะเบียนเสร็จสมบูรณ์
- `add_to_cart` - เพิ่มสินค้าในตะกร้า
- `initiate_checkout` - เริ่มต้นการชำระเงิน
- `page_engagement` - การมีส่วนร่วมกับเพจ
- `post_engagement` - การมีส่วนร่วมกับโพสต์
- `link_click` - คลิกลิงก์
- `onsite_conversion.messaging_first_reply` - การตอบกลับข้อความครั้งแรก

## Environment Variables

ตั้งค่า environment variables ใน `.env`:

```env
# Facebook Ads API
FACEBOOK_ACCESS_TOKEN=your_access_token_here
FACEBOOK_AD_ACCOUNT_ID=act_1234567890
```

### How to Get Facebook Access Token

1. ไปที่ [Facebook Developers](https://developers.facebook.com/)
2. สร้าง App หรือใช้ App ที่มีอยู่
3. ไปที่ Tools > Graph API Explorer
4. เลือก App และ Permissions ที่ต้องการ:
   - `ads_read`
   - `ads_management`
   - `business_management`
5. คัดลอก Access Token
6. แนะนำให้ใช้ **Long-Lived Access Token** (valid for 60 days)

### How to Get Ad Account ID

1. ไปที่ [Facebook Ads Manager](https://business.facebook.com/adsmanager)
2. เลือก Ad Account ที่ต้องการ
3. ดูที่ URL จะมี `act=123456789`
4. Ad Account ID คือ `act_123456789`

## Testing

### Test with curl

```bash
# Test basic endpoint
curl "http://localhost:5000/api/facebook-ads-campaigns"

# Test with parameters
curl "http://localhost:5000/api/facebook-ads-campaigns?level=campaign&date_preset=last_7d"

# Test with custom date range
curl "http://localhost:5000/api/facebook-ads-campaigns?time_range=%7B%22since%22%3A%222025-11-01%22%2C%22until%22%3A%222025-11-17%22%7D"
```

### Test with Python

```python
import requests

# Basic request
response = requests.get('http://localhost:5000/api/facebook-ads-campaigns')
data = response.json()
print(data)

# With parameters
params = {
    'level': 'campaign',
    'date_preset': 'last_7d',
    'time_increment': '1'
}
response = requests.get('http://localhost:5000/api/facebook-ads-campaigns', params=params)
data = response.json()
print(data['summary'])
```

### Test with JavaScript

```javascript
// Basic request
fetch("http://localhost:5000/api/facebook-ads-campaigns")
  .then((response) => response.json())
  .then((data) => console.log(data));

// With parameters
const params = new URLSearchParams({
  level: "campaign",
  date_preset: "last_7d",
  time_increment: "1",
});

fetch(`http://localhost:5000/api/facebook-ads-campaigns?${params}`)
  .then((response) => response.json())
  .then((data) => console.log(data.summary));
```

## Common Issues & Solutions

### Issue 1: Invalid Access Token

**Error:** `Invalid OAuth 2.0 Access Token`

**Solution:**

- ตรวจสอบว่า Access Token ยังไม่หมดอายุ
- สร้าง Long-Lived Access Token ใหม่
- ตรวจสอบ Permissions ของ Token

### Issue 2: Invalid Ad Account ID

**Error:** `(#100) Invalid Ad Account ID`

**Solution:**

- ตรวจสอบว่า Ad Account ID เริ่มต้นด้วย `act_`
- ตรวจสอบว่า User มีสิทธิ์เข้าถึง Ad Account นี้

### Issue 3: Rate Limit

**Error:** `(#80004) There have been too many calls to this ad account`

**Solution:**

- รอสักครู่แล้วลองใหม่
- ลดจำนวนการเรียก API
- ใช้ Cache เพื่อลดการเรียก API

### Issue 4: Missing Permissions

**Error:** `(#10) Permission denied`

**Solution:**

- ตรวจสอบว่า Access Token มี Permissions ที่จำเป็น:
  - `ads_read`
  - `ads_management`
  - `business_management`

## Best Practices

1. **Use Caching** - เก็บผลลัพธ์ที่ได้ไว้ในระบบ cache
2. **Rate Limiting** - อย่าเรียก API บ่อยเกินไป
3. **Error Handling** - จัดการ error ให้ดี
4. **Long-Lived Tokens** - ใช้ Long-Lived Access Token แทน Short-Lived
5. **Date Range** - จำกัดช่วงเวลาให้เหมาะสม ไม่ควรดึงข้อมูลย้อนหลังมากเกินไป
6. **Level Selection** - เลือก level ที่เหมาะสมกับความต้องการ (campaign, adset, ad)

## API Limitations

- Facebook Marketing API มี Rate Limit ตาม Ad Account
- Access Token มีอายุ 60 วัน (Long-Lived Token)
- บาง metrics อาจไม่มีค่าสำหรับบาง campaigns
- ข้อมูล real-time อาจมี delay 15-30 นาที

## Resources

- [Facebook Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)
- [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer)
- [Facebook Business SDK for Python](https://github.com/facebook/facebook-python-business-sdk)

## Support

หากพบปัญหาหรือต้องการความช่วยเหลือ:

1. ตรวจสอบ logs ใน terminal
2. ดู error message ใน response
3. ตรวจสอบ Facebook Ads Manager ว่ามีข้อมูลหรือไม่
4. ทดสอบใน Graph API Explorer ก่อน
