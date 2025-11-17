# 🐍 Python API - Quick Start Guide

## 📋 สรุป

Python API นี้ทำหน้าที่ดึงข้อมูลจาก Google Sheets "Film data" และให้บริการผ่าน REST API

## 🚀 วิธีรัน (Local Development)

### 1. ติดตั้ง Dependencies

```powershell
cd python-api
pip install -r requirements.txt
```

### 2. ตรวจสอบไฟล์ .env

ไฟล์ `.env` ถูกสร้างให้อัตโนมัติแล้วโดยมีข้อมูลจาก `.env.local` หลัก

ตรวจสอบว่ามีค่าต่อไปนี้:

- ✅ `GOOGLE_SPREADSHEET_ID`
- ✅ `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- ✅ `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY`

### 3. รัน Python API

```powershell
python app.py
```

หรือ

```powershell
flask run
```

API จะรันที่: `http://localhost:5000`

### 4. ทดสอบ API

เปิดเบราว์เซอร์หรือใช้ PowerShell:

```powershell
# Health check
curl http://localhost:5000/health

# ดึงข้อมูลทั้งหมด
curl http://localhost:5000/api/film-data
```

### 5. รัน Next.js (Terminal แยก)

```powershell
# ใน terminal ใหม่ กลับไปที่ root
cd ..
npm run dev
```

### 6. เปิดหน้าเว็บ

ไปที่: `http://localhost:3000/performance-surgery-schedule`

---

## 📡 API Endpoints

| Endpoint                      | Method | คำอธิบาย                                                       |
| ----------------------------- | ------ | -------------------------------------------------------------- |
| `/`                           | GET    | ข้อมูลเกี่ยวกับ API                                            |
| `/health`                     | GET    | Health check และ cache status                                  |
| `/api/film-data`              | GET    | ดึงข้อมูลจาก Google Sheets                                     |
| `/api/clear-cache`            | POST   | Clear cache (รีเฟรชข้อมูลใหม่)                                 |
| `/api/facebook-ads-campaigns` | GET    | ดึงข้อมูลจาก Facebook Ads Manager                              |
| `/api/facebook-ads-manager`   | GET    | Alias สำหรับ Facebook Ads (เหมือน /api/facebook-ads-campaigns) |
| `/api/google-sheets-data`     | GET    | ดึงข้อมูลจากชีท 'เคสได้ชื่อเบอร์'                              |
| `/api/google-ads`             | GET    | ดึงข้อมูลจาก Google Ads                                        |
| `/run-time`                   | GET    | ดึงสถิติการโทรจากชีท 'สรุป call_AI'                            |
| `/N_SaleIncentive_data`       | GET    | ดึงข้อมูล Sale Incentive                                       |
| `/data_bjh`                   | GET    | ดึงข้อมูล Leads จากฐานข้อมูล PostgreSQL                        |

---

## 🎯 Deploy บน Railway.com

### ขั้นตอนที่ 1: เตรียม Code

1. **ตรวจสอบไฟล์ที่จำเป็น** ✅

   - `app.py` - Main Flask application
   - `requirements.txt` - Python dependencies
   - `Procfile` - Railway deployment config
   - `runtime.txt` - Python version
   - `.env.example` - Template สำหรับ environment variables

2. **Push Code ขึ้น GitHub**

```powershell
git add python-api/
git commit -m "Update Python API for Railway deployment"
git push origin main
```

### ขั้นตอนที่ 2: สร้าง Railway Project

1. ไปที่ **https://railway.app**
2. **Sign in** ด้วย GitHub
3. คลิก **"New Project"**
4. เลือก **"Deploy from GitHub repo"**
5. เลือก repository ของคุณ (เช่น `Git_API_Python`)
6. Railway จะ detect Python project อัตโนมัติ

### ขั้นตอนที่ 3: ตั้งค่า Root Directory (ถ้า API อยู่ใน subfolder)

ถ้า API อยู่ใน folder `python-api`:

1. ไปที่ **Settings** tab
2. ตั้งค่า **Root Directory** = `python-api`
3. หรือตั้งค่าใน **Build Command**: (ไม่ต้องตั้งถ้า root directory ถูกต้อง)

### ขั้นตอนที่ 4: ตั้งค่า Environment Variables

ใน Railway Dashboard → **Variables** tab, เพิ่มตัวแปรเหล่านี้:

#### ✅ ตัวแปรที่จำเป็น (Required):

```env
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASC...
(คัดลอกทั้ง private key จากไฟล์ .env)
...
-----END PRIVATE KEY-----
```

#### ⚙️ ตัวแปรเสริม (Optional):

```env
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_PRIVATE_KEY_ID=your-private-key-id
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_CERT_URL=your-cert-url
FLASK_ENV=production
CACHE_DURATION=30
```

⚠️ **สำคัญมาก**:

- **Private Key**: ต้องใส่แบบ **multi-line** จริงๆ (กด Enter แบ่งบรรทัด)
- หรือใส่แบบ **JSON string** ที่มี `\n` แทน newline
- **ห้าม** copy-paste แบบมี escape characters ผิดรูปแบบ

**วิธีใส่ Private Key ที่ถูกต้อง:**

```
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
(กด Enter แบ่งบรรทัด)
...
-----END PRIVATE KEY-----
```

### ขั้นตอนที่ 5: Deploy

1. Railway จะ **auto-deploy** เมื่อตั้งค่าเสร็จ
2. รอ build logs ประมาณ 1-2 นาที
3. เมื่อ deploy สำเร็จ คุณจะได้ URL เช่น:
   ```
   https://your-app-name.up.railway.app
   ```

### ขั้นตอนที่ 6: ทดสอบ API

เปิดเบราว์เซอร์หรือใช้ PowerShell:

```powershell
# Root endpoint
curl https://your-app.up.railway.app/

# Health check
curl https://your-app.up.railway.app/health

# Get data
curl https://your-app.up.railway.app/api/film-data
```

### ขั้นตอนที่ 7: เชื่อมต่อกับ Frontend (Next.js/React)

อัพเดท environment variable ใน frontend:

**ตัวอย่างใน Next.js (.env.local):**

```env
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
```

**ตัวอย่างการเรียกใช้:**

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchData() {
  const response = await fetch(`${API_URL}/api/film-data`);
  const data = await response.json();
  return data;
}
```

---

## 🔍 Troubleshooting

### ปัญหา: ImportError หรือ ModuleNotFoundError

```powershell
pip install -r requirements.txt --force-reinstall
```

### ปัญหา: Google Sheets 403 Forbidden

1. ตรวจสอบว่า Service Account Email ถูก share เข้า Google Sheet แล้ว
2. ตรวจสอบว่า Private Key ถูกต้อง (มี `-----BEGIN PRIVATE KEY-----`)
3. ตรวจสอบว่าชีทชื่อ "Film data" มีอยู่จริง

### ปัญหา: Port 5000 ถูกใช้งานแล้ว

แก้ไข `.env`:

```env
PORT=5001
```

และแก้ `.env.local` ของ Next.js:

```env
PYTHON_API_URL=http://localhost:5001
```

### ปัญหา: Next.js ไม่เชื่อมต่อกับ Python API

1. ตรวจสอบว่า Python API รันอยู่
2. ตรวจสอบ `PYTHON_API_URL` ใน `.env.local`
3. ดู Console logs ใน Browser DevTools และ Python API terminal

---

## 📦 ไฟล์ที่สร้างแล้ว

```
python-api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Railway/Heroku deployment
├── runtime.txt        # Python version
├── .env               # Environment variables (local)
├── .env.example       # Environment template
└── .gitignore         # Git ignore file
```

---

## 🎉 เสร็จสิ้น!

ตอนนี้คุณมี Python API ที่:

- ✅ อ่านข้อมูลจาก Google Sheets
- ✅ มี caching 30 วินาที
- ✅ พร้อม deploy บน Railway
- ✅ เชื่อมต่อกับ Next.js ได้

---

## 📚 เอกสารเพิ่มเติม

- `PYTHON_API_RAILWAY_GUIDE.md` - คู่มือ deploy บน Railway
- `PYTHON_API_SURGERY_SCHEDULE_GUIDE.md` - คู่มือการใช้งานครบวงจร
- `FACEBOOK_ADS_MANAGER_GUIDE.md` - คู่มือการใช้งาน Facebook Ads Manager API
- `GOOGLE_ADS_SETUP.md` - คู่มือการตั้งค่า Google Ads API
- `N_SALE_INCENTIVE_API_GUIDE.md` - คู่มือการใช้งาน Sale Incentive API
