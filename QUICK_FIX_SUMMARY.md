# ✅ สรุปการแก้ไข Facebook Ads API บน Railway

## 📅 วันที่: 17 พฤศจิกายน 2025

## 🎯 ปัญหา

- URL: `https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns`
- Error: `404 Application not found`

## ✅ สิ่งที่ทำไปแล้ว

### 1. แก้ไข Dependencies (`requirements.txt`)

```diff
- google-ads==21.3.0
+ google-ads==22.1.0
+ grpcio==1.62.3
+ grpcio-status==1.62.3
+ protobuf==4.25.8
```

### 2. ปรับปรุง Dockerfile

```dockerfile
# เพิ่ม timeout และ retry
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=300 --retries 5 -r requirements.txt
```

### 3. แก้ไข Google Ads API (`app.py`)

```python
# รองรับ v17
ga_service = client.get_service('GoogleAdsService')
```

### 4. เพิ่มไฟล์ใหม่

- ✅ `railway.json` - Railway configuration
- ✅ `.dockerignore` - Optimize build
- ✅ `RAILWAY_FACEBOOK_ADS_FIX.md` - คู่มือแก้ไข
- ✅ `DOCKER_BUILD_FIX.md` - คู่มือแก้ปัญหา Docker

### 5. Push ไป GitHub

```bash
git add .
git commit -m "Fix Facebook Ads API deployment on Railway"
git push origin main
```

## ⏳ ขั้นตอนถัดไป

### 1. รอ Railway Auto-Deploy (1-5 นาที)

Railway จะ detect การ push ไป GitHub และ auto-deploy

**ตรวจสอบ:**

- ไปที่: https://railway.app/project/believable-ambition-production
- ดูที่ **Deployments** tab
- รอจนสถานะเป็น **Active** หรือ **Success**

### 2. ตรวจสอบ Environment Variables

ไปที่ **Variables** tab และตรวจสอบว่ามีครบ:

**สำคัญที่สุด:**

```env
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBP...
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166
```

**อื่นๆ:**

```env
FLASK_ENV=production
PORT=5000
GOOGLE_SPREADSHEET_ID=...
GOOGLE_SERVICE_ACCOUNT_EMAIL=...
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
```

### 3. ทดสอบ API

หลังจาก deploy เสร็จ:

```bash
# Test 1: Root endpoint
curl https://believable-ambition-production.up.railway.app/

# Test 2: Health check
curl https://believable-ambition-production.up.railway.app/health

# Test 3: Facebook Ads API
curl https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns
```

**Expected Response:**

```json
{
  "success": true,
  "level": "campaign",
  "data": [...],
  "summary": {
    "total_spend": 100.50,
    "total_impressions": 10000,
    "total_clicks": 500
  }
}
```

## 🔍 Troubleshooting

### ถ้ายังเจอ 404:

1. **ตรวจสอบ Deployment Logs:**

   - Railway Dashboard → Deployments → View Logs
   - หา error messages

2. **Redeploy Manually:**

   - Deployments tab → คลิก "Redeploy"

3. **ตรวจสอบ Settings:**
   - Settings tab → Root Directory: **ว่างเปล่า**
   - Builder: **Dockerfile**

### ถ้าเจอ 500 Internal Server Error:

1. **ตรวจสอบ Environment Variables**

   - ครบทุกตัวหรือไม่?
   - Facebook Access Token ยังใช้ได้อยู่?

2. **ดู Runtime Logs:**
   - Railway Dashboard → Logs tab
   - หา Python error messages

### ถ้าเจอ Facebook API Error:

**Error:** `Invalid OAuth 2.0 Access Token`

**แก้ไข:**

1. Facebook Access Token หมดอายุ (60 วัน)
2. ต้องสร้าง Long-Lived Token ใหม่
3. อัปเดทใน Railway Variables
4. Redeploy

**วิธีสร้าง Long-Lived Token:**

1. ไปที่: https://developers.facebook.com/tools/explorer
2. เลือก App และ Permissions: `ads_read`, `ads_management`
3. Generate Access Token
4. ใช้ Graph API Explorer แปลงเป็น Long-Lived:
   ```
   GET /oauth/access_token?
     grant_type=fb_exchange_token&
     client_id={app-id}&
     client_secret={app-secret}&
     fb_exchange_token={short-lived-token}
   ```

## 📊 Build Progress

**Expected Timeline:**

- ⏰ Push to GitHub: ทันที
- ⏰ Railway detect & start build: 30 วินาที
- ⏰ Install dependencies: 2-3 นาที
- ⏰ Build Docker image: 1-2 นาที
- ⏰ Deploy & start: 30 วินาที
- **✅ Total: ~3-5 นาที**

## 📱 Quick Check Commands

```bash
# PowerShell
Invoke-RestMethod -Uri "https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns" | ConvertTo-Json

# Bash/Git Bash
curl https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns | jq

# Browser
https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns
```

## 📚 เอกสารเพิ่มเติม

- `RAILWAY_FACEBOOK_ADS_FIX.md` - คู่มือแก้ไขละเอียด
- `DOCKER_BUILD_FIX.md` - คู่มือแก้ปัญหา Docker build
- `python-api/FACEBOOK_ADS_MANAGER_GUIDE.md` - API Documentation
- `python-api/FACEBOOK_ADS_CHANGES.md` - รายละเอียดการเปลี่ยนแปลง

## ✨ Status

- ✅ Code pushed to GitHub
- ⏳ Waiting for Railway auto-deploy
- ⏳ ตรวจสอบ deployment logs
- ⏳ ทดสอบ API endpoints

**Next:** รอ 3-5 นาทีแล้วทดสอบ API!
