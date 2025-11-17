# สรุปการแก้ไข Facebook Ads Manager API

## 📅 วันที่: 17 พฤศจิกายน 2025

## 🎯 สิ่งที่ได้แก้ไข

### 1. ปรับปรุง Facebook Ads API Endpoint (`/api/facebook-ads-campaigns`)

#### การเปลี่ยนแปลงหลัก:

1. **เพิ่ม Conversions Field**

   - เพิ่มการดึง `conversions` และ `conversion_values` จาก Facebook API
   - ประมวลผล conversions จากทั้ง field `conversions` และ `actions`
   - คำนวณ `total_conversions` สำหรับแต่ละ campaign/adset/ad

2. **ปรับปรุง Actions Processing**

   - สร้าง `processed_actions` dictionary เพื่อให้เข้าถึง actions ได้ง่ายขึ้น
   - นับ leads และ purchases แยกต่างหาก
   - แสดงผลใน summary ที่ชัดเจนขึ้น

3. **เพิ่ม Metrics ใน Summary**

   - `total_conversions` - ยอดรวม conversions
   - `total_leads` - ยอดรวม leads
   - `total_purchase` - ยอดรวม purchases
   - `cost_per_result` - ค่าใช้จ่ายต่อ conversion
   - `frequency` - ค่าเฉลี่ย frequency

4. **ปรับปรุง Error Handling**

   - เพิ่ม logging ที่ชัดเจนขึ้น
   - แสดง error message ที่เข้าใจง่ายขึ้น

5. **เพิ่ม Calculated Metrics**
   - `cost_per_result` สำหรับแต่ละ record
   - `total_conversions` ที่รวมจาก actions และ conversions field

### 2. เพิ่ม Alias Endpoint

สร้าง endpoint ใหม่ `/api/facebook-ads-manager` ที่เป็น alias ของ `/api/facebook-ads-campaigns` เพื่อความสะดวกในการใช้งาน

### 3. อัปเดต Dependencies

อัปเดต `requirements.txt`:

- `facebook-business==19.0.0` → `facebook-business==20.0.3`

### 4. สร้างเอกสารคู่มือ

สร้าง `FACEBOOK_ADS_MANAGER_GUIDE.md` ที่มีข้อมูลครบถ้วน:

- คำอธิบาย API endpoints
- Query parameters
- Response format
- ตัวอย่างการใช้งาน
- Available metrics
- Action types
- Environment variables setup
- วิธีการ test
- Troubleshooting
- Best practices

### 5. อัปเดต README.md

เพิ่มข้อมูลใน README.md:

- เพิ่ม Facebook Ads endpoints ในตาราง API Endpoints
- เพิ่มลิงก์ไปยัง `FACEBOOK_ADS_MANAGER_GUIDE.md`

### 6. สร้าง Test Script

สร้าง `test_facebook_ads.py` สำหรับทดสอบ API:

- Test root endpoint
- Test basic Facebook Ads
- Test with different date presets
- Test daily breakdown
- Test adset level
- Test alias endpoint

## 📊 ฟีเจอร์ที่เพิ่มเข้ามา

### Query Parameters ที่รองรับ:

1. **level** (default: "campaign")

   - `campaign` - ระดับ Campaign
   - `adset` - ระดับ Ad Set
   - `ad` - ระดับ Ad

2. **date_preset** (default: "today")

   - `today` - วันนี้
   - `yesterday` - เมื่อวาน
   - `last_7d` - 7 วันที่แล้ว
   - `last_30d` - 30 วันที่แล้ว
   - `this_month` - เดือนนี้
   - `last_month` - เดือนที่แล้ว

3. **time_range** (JSON string)

   - กำหนดช่วงเวลาแบบ custom: `{"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}`

4. **time_increment**

   - `1` - แสดงผลแบบรายวัน
   - `monthly` - แสดงผลแบบรายเดือน

5. **fields** (comma-separated)
   - เพิ่มฟิลด์เพิ่มเติมที่ต้องการ

### Metrics ที่ส่งกลับ:

#### Data Fields:

- Campaign/AdSet/Ad information
- Spend, Impressions, Clicks
- CTR, CPC, CPM, CPP
- Reach, Frequency
- Actions (with processed_actions dictionary)
- Conversions (with total_conversions)
- Cost per result
- Date range

#### Summary Fields:

- total_spend
- total_impressions
- total_reach
- total_clicks
- total_conversions
- total_leads
- total_purchase
- average_cpc
- average_ctr
- cost_per_result
- frequency

## 🔧 การใช้งาน

### ตัวอย่างการเรียก API:

```bash
# Basic - Today's data
GET /api/facebook-ads-campaigns

# Last 7 days
GET /api/facebook-ads-campaigns?date_preset=last_7d

# Custom date range
GET /api/facebook-ads-campaigns?time_range={"since":"2025-11-01","until":"2025-11-17"}

# AdSet level with daily breakdown
GET /api/facebook-ads-campaigns?level=adset&date_preset=last_7d&time_increment=1

# Using alias endpoint
GET /api/facebook-ads-manager?date_preset=today
```

### Response Example:

```json
{
  "success": true,
  "level": "campaign",
  "date_preset": "today",
  "time_range": {
    "since": "2025-11-17",
    "until": "2025-11-17"
  },
  "data": [...],
  "summary": {
    "total_spend": 100.50,
    "total_impressions": 10000,
    "total_clicks": 500,
    "total_conversions": 30,
    "total_leads": 25,
    "total_purchase": 5,
    "average_cpc": 0.20,
    "average_ctr": 5.00,
    "cost_per_result": 3.35,
    "frequency": 1.25
  },
  "total_records": 1,
  "timestamp": "2025-11-17T10:30:00"
}
```

## ⚙️ Environment Variables

ต้องตั้งค่าใน `.env`:

```env
FACEBOOK_ACCESS_TOKEN=your_access_token_here
FACEBOOK_AD_ACCOUNT_ID=act_1234567890
```

## 🧪 การทดสอบ

รันสคริปต์ทดสอบ:

```bash
# ต้องเปิด API server ก่อน
python app.py

# จากนั้นใน terminal ใหม่
python test_facebook_ads.py
```

## 📝 ไฟล์ที่เพิ่ม/แก้ไข

### ไฟล์ที่แก้ไข:

1. `app.py` - ปรับปรุง Facebook Ads endpoint
2. `requirements.txt` - อัปเดต facebook-business version
3. `README.md` - เพิ่มข้อมูล endpoints และเอกสาร

### ไฟล์ใหม่:

1. `FACEBOOK_ADS_MANAGER_GUIDE.md` - คู่มือการใช้งานครบถ้วน
2. `test_facebook_ads.py` - สคริปต์ทดสอบ
3. `FACEBOOK_ADS_CHANGES.md` - เอกสารนี้

## 🎯 การ Deploy

### สำหรับ Railway:

1. **อัปเดต Environment Variables:**

   ```env
   FACEBOOK_ACCESS_TOKEN=your_access_token
   FACEBOOK_AD_ACCOUNT_ID=act_1234567890
   ```

2. **Push code:**

   ```bash
   git add .
   git commit -m "Update Facebook Ads Manager API"
   git push origin main
   ```

3. Railway จะ auto-deploy

### ทดสอบหลัง Deploy:

```bash
curl https://your-app.up.railway.app/api/facebook-ads-campaigns
```

## ✅ Testing Checklist

- [x] API endpoint ทำงานได้
- [x] Query parameters ทำงานถูกต้อง
- [x] Response format ถูกต้อง
- [x] Summary metrics ถูกต้อง
- [x] Error handling ทำงาน
- [x] Alias endpoint ทำงาน
- [x] เอกสารครบถ้วน
- [x] Test script พร้อมใช้งาน

## 🚨 ข้อควรระวัง

1. **Access Token Expiration**

   - Facebook Access Token หมดอายุใน 60 วัน (Long-Lived Token)
   - ต้องสร้าง token ใหม่เมื่อหมดอายุ

2. **Rate Limiting**

   - Facebook มี rate limit ตาม Ad Account
   - ควรใช้ cache เมื่อเรียกข้อมูลบ่อยๆ

3. **Permissions**

   - Token ต้องมี permissions: `ads_read`, `ads_management`, `business_management`

4. **Data Accuracy**
   - ข้อมูล real-time อาจมี delay 15-30 นาที
   - ควรใช้ข้อมูลย้อนหลัง 1 วันสำหรับความแม่นยำ

## 📚 เอกสารอ้างอิง

- [Facebook Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)
- [Facebook Business SDK for Python](https://github.com/facebook/facebook-python-business-sdk)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer)

## 🎉 สรุป

การแก้ไขนี้ทำให้ Facebook Ads Manager API:

- ✅ มีข้อมูล conversions ครบถ้วน
- ✅ มี summary metrics ที่เป็นประโยชน์
- ✅ รองรับ query parameters หลากหลาย
- ✅ มีเอกสารคู่มือครบถ้วน
- ✅ มี test script สำหรับทดสอบ
- ✅ พร้อม deploy บน Railway
