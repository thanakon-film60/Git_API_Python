# วิธีแก้ไข Facebook Ads API บน Railway

## 🔍 ปัญหาที่พบ

เมื่อเข้า: `https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns`

```json
{
  "status": "error",
  "code": 404,
  "message": "Application not found"
}
```

## ✅ สาเหตุและวิธีแก้ไข

### สาเหตุที่เป็นไปได้:

1. ✅ Application ถูก undeploy หรือ stopped
2. ✅ Environment variables ไม่ครบ
3. ✅ Dockerfile หรือ build มีปัญหา
4. ✅ Port configuration ไม่ถูกต้อง
5. ✅ Code ยังไม่ได้ push ไป GitHub

## 🚀 วิธีแก้ไขทีละขั้นตอน

### ขั้นตอนที่ 1: ตรวจสอบและ Push Code ล่าสุด

```bash
# 1. ตรวจสอบ status
git status

# 2. Add ไฟล์ทั้งหมด
git add .

# 3. Commit
git commit -m "Fix Facebook Ads API and update dependencies"

# 4. Push to GitHub
git push origin main
```

### ขั้นตอนที่ 2: ตรวจสอบไฟล์ที่จำเป็น

ตรวจสอบว่ามีไฟล์เหล่านี้:

- ✅ `Dockerfile` - สำหรับ build Docker image
- ✅ `railway.json` - กำหนดค่า Railway
- ✅ `python-api/requirements.txt` - Python dependencies
- ✅ `python-api/app.py` - Main application
- ✅ `.dockerignore` - ลด build size

### ขั้นตอนที่ 3: ตั้งค่า Environment Variables บน Railway

ไปที่: [Railway Dashboard](https://railway.app/project/believable-ambition-production)

#### Variables ที่จำเป็นสำหรับ Facebook Ads:

```env
# Facebook Ads API (Required)
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBP5kZBuQfpSzBZATCVdS1poTSVJasZCZBlB3RrCKN3fJ6NMAn8GdOONsoX7Awf1yNjZAlUAs6SNdnsfGnwzrFCQkzGDUQb3tK86NKHZAzed1XugUuYyV5gxPyIZBYJS996bXzfW1wVmdjgUxsOJoFUF8tykzoeF3BSXmUcNYZBkF7ZCwRBtxdpsAvKFNQ9
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166
```

#### Variables อื่นๆ:

```env
# Google Sheets
GOOGLE_SPREADSHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SERVICE_ACCOUNT_EMAIL=web-sheets-reader@name-tel-dev.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...คัดลอกทั้งหมด...
-----END PRIVATE KEY-----"
GOOGLE_PROJECT_ID=name-tel-dev

# Google Ads
GOOGLE_ADS_CLIENT_ID=310364673147-1tbnkgujso2smo0t0qsqjd95n9oorbe9.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=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
GOOGLE_ADS_DEVELOPER_TOKEN=8KWFw-bsGe920_kfcQuT_g
GOOGLE_ADS_REFRESH_TOKEN=1//0guXuiYplyga8CgYIARAAGBASNwF-L9Ir8tKM-AjQ5EVTjDy0GvYh8kDNeTqZ1kWx_VbgvygQ6ueh4grcQ0LwI201x5t87uK7YkA
GOOGLE_ADS_CUSTOMER_ID=4275609411

# Flask
FLASK_ENV=production
PORT=5000
CACHE_DURATION=30
```

### ขั้นตอนที่ 4: ตรวจสอบ Railway Settings

1. **ไปที่ Railway Dashboard** → เลือก Project
2. **ไปที่ Settings tab:**
   - ✅ Root Directory: **ว่างเปล่า** (ใช้ root ของ repo)
   - ✅ Build Command: **ว่างเปล่า** (ใช้ Dockerfile)
   - ✅ Start Command: **ว่างเปล่า** (ใช้ CMD ใน Dockerfile)
   - ✅ Builder: **Dockerfile**

### ขั้นตอนที่ 5: Manual Redeploy

1. ไปที่ **Deployments** tab
2. คลิก **Redeploy** หรือ **Deploy**
3. รอให้ build เสร็จ (ประมาณ 3-5 นาที)

### ขั้นตอนที่ 6: ตรวจสอบ Logs

ระหว่าง build, ดู logs ว่ามี error หรือไม่:

```bash
# หา error เหล่านี้:
✅ "Installing collected packages..." - dependencies ติดตั้งสำเร็จ
✅ "Successfully installed..." - build สำเร็จ
❌ "TimeoutError" - ต้อง redeploy ใหม่
❌ "ModuleNotFoundError" - dependencies ไม่ครบ
❌ "Connection refused" - environment variables ไม่ถูกต้อง
```

### ขั้นตอนที่ 7: ทดสอบ API

หลังจาก deploy สำเร็จ:

```bash
# 1. ทดสอบ root endpoint
curl https://believable-ambition-production.up.railway.app/

# 2. ทดสอบ health check
curl https://believable-ambition-production.up.railway.app/health

# 3. ทดสอบ Facebook Ads API
curl https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns
```

## 🔧 Quick Fix Commands

### Push Code และ Deploy:

```bash
# ใน Git Bash หรือ PowerShell
cd C:\Users\Pac-Man45\Documents\GitHub\Git_API_Python

# Add ไฟล์ทั้งหมด
git add .

# Commit with descriptive message
git commit -m "Fix Facebook Ads API deployment on Railway
- Update requirements.txt with compatible versions
- Fix Dockerfile with increased timeout
- Add railway.json configuration
- Update app.py for Google Ads API v17"

# Push to GitHub
git push origin main

# Railway จะ auto-deploy ภายใน 1-2 นาที
```

### ตรวจสอบ Deployment Status:

```bash
# ใช้ Railway CLI (ถ้าติดตั้งแล้ว)
railway logs

# หรือดูใน Railway Dashboard
# https://railway.app/project/believable-ambition-production/deployments
```

## 📋 Checklist ก่อน Deploy

- [ ] Code ล่าสุด commit และ push แล้ว
- [ ] `requirements.txt` มี dependencies ครบ
- [ ] `Dockerfile` มีการตั้งค่าที่ถูกต้อง
- [ ] `railway.json` มีอยู่ใน root
- [ ] Environment variables ครบทุกตัว
- [ ] Facebook Access Token ยังไม่หมดอายุ
- [ ] Port configuration ถูกต้อง (5000)

## 🐛 Common Issues

### Issue 1: 404 Application Not Found

**สาเหตุ:** Application ไม่ได้รัน

**แก้ไข:**
1. ตรวจสอบ logs ใน Railway
2. Redeploy ใหม่
3. ตรวจสอบ Dockerfile

### Issue 2: 500 Internal Server Error

**สาเหตุ:** Code มี error หรือ environment variables ไม่ครบ

**แก้ไข:**
1. ดู deployment logs
2. ตรวจสอบ environment variables
3. ทดสอบใน local ก่อน

### Issue 3: Facebook API Error

**สาเหตุ:** Access token หมดอายุหรือ invalid

**แก้ไข:**
1. สร้าง Long-Lived Access Token ใหม่
2. อัปเดทใน Railway Variables
3. Redeploy

### Issue 4: Build Timeout

**สาเหตุ:** Download dependencies นานเกินไป

**แก้ไข:**
1. Redeploy ใหม่ (อาจเป็นปัญหาชั่วคราว)
2. ตรวจสอบว่า `Dockerfile` มี `--default-timeout=300`

## 🎯 Expected Results

หลังจากแก้ไขสำเร็จ:

### Root Endpoint:
```bash
curl https://believable-ambition-production.up.railway.app/
```

**Response:**
```json
{
  "status": "ok",
  "message": "Python API for Performance Surgery Schedule",
  "version": "1.0.0",
  "environment": "production",
  "endpoints": {
    "/api/facebook-ads-campaigns": "Get Facebook Ads campaigns data",
    ...
  }
}
```

### Facebook Ads Endpoint:
```bash
curl https://believable-ambition-production.up.railway.app/api/facebook-ads-campaigns
```

**Response:**
```json
{
  "success": true,
  "level": "campaign",
  "data": [...],
  "summary": {
    "total_spend": 100.50,
    "total_impressions": 10000,
    ...
  }
}
```

## 📚 Resources

- [Railway Documentation](https://docs.railway.app/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Facebook Marketing API](https://developers.facebook.com/docs/marketing-apis)

## 💡 Pro Tips

1. **Use Railway CLI** สำหรับ deploy เร็วขึ้น:
   ```bash
   npm install -g @railway/cli
   railway login
   railway up
   ```

2. **Monitor Logs** ตลอดเวลาเพื่อดู errors:
   ```bash
   railway logs --follow
   ```

3. **Test Locally First** ก่อน deploy ทุกครั้ง:
   ```bash
   docker build -t test-api .
   docker run -p 5000:5000 --env-file python-api/.env test-api
   ```

## 🆘 Need Help?

ถ้ายังมีปัญหา:
1. ดู Railway deployment logs
2. ตรวจสอบ GitHub Actions (ถ้ามี)
3. ทดสอบ local Docker build
4. ตรวจสอบ environment variables อีกครั้ง
