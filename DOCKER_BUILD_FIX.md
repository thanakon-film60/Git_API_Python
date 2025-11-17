# แก้ไขปัญหา Docker Build และ Dependencies

## 📅 วันที่: 17 พฤศจิกายน 2025

## 🐛 ปัญหาที่พบ

### 1. Timeout ระหว่าง pip install

```
ERROR: Exception:
TimeoutError: The read operation timed out
```

### 2. Dependency Conflict

```
INFO: pip is looking at multiple versions of grpcio-status to determine which version is compatible with other requirements.
```

## ✅ การแก้ไข

### 1. อัปเดต `requirements.txt`

**เปลี่ยนจาก:**

```txt
google-ads==21.3.0
```

**เป็น:**

```txt
google-ads==22.1.0
grpcio==1.62.3
grpcio-status==1.62.3
protobuf==4.25.8
```

**เหตุผล:**

- ใช้ `google-ads==22.1.0` ที่เสถียรกว่าและมี dependencies ที่ชัดเจน
- ระบุ version ของ `grpcio` และ `grpcio-status` ให้ตรงกันเพื่อหลีกเลี่ยง conflict
- ระบุ `protobuf` version ที่เข้ากันได้

### 2. ปรับปรุง `Dockerfile`

**เปลี่ยนจาก:**

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**เป็น:**

```dockerfile
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=300 --retries 5 -r requirements.txt
```

**เหตุผล:**

- อัปเดต pip เป็น version ล่าสุด
- เพิ่ม timeout เป็น 300 วินาที (5 นาที)
- เพิ่มจำนวนครั้งในการ retry เป็น 5 ครั้ง
- ช่วยให้ download packages ขนาดใหญ่ได้สำเร็จ

### 3. แก้ไข Google Ads API Version

**ใน `app.py` เปลี่ยนจาก:**

```python
ga_service = client.get_service('GoogleAdsService', version='v13')
```

**เป็น:**

```python
ga_service = client.get_service('GoogleAdsService')
```

**เหตุผล:**

- `google-ads==22.1.0` ใช้ API version ใหม่กว่า (v17)
- ไม่ระบุ version จะใช้ default version ที่เหมาะสม

### 4. สร้าง `.dockerignore`

สร้างไฟล์ `.dockerignore` เพื่อ:

- ลดขนาด build context
- เร่งความเร็วในการ build
- ไม่ copy ไฟล์ที่ไม่จำเป็นเข้า Docker image

## 🔧 รายละเอียด Dependencies

### Compatible Versions:

```txt
Flask==3.0.3
flask-cors==4.0.0
gspread==6.1.2
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
python-dotenv==1.0.1
gunicorn==22.0.0
requests==2.31.0
facebook-business==20.0.3
google-ads==22.1.0          # ← Updated
grpcio==1.62.3              # ← New
grpcio-status==1.62.3       # ← New
protobuf==4.25.8            # ← New
psycopg2-binary==2.9.9
```

## 🧪 การทดสอบ

### Test Locally:

```bash
# ติดตั้ง dependencies ใหม่
cd python-api
pip install -r requirements.txt

# ทดสอบรัน API
python app.py

# ทดสอบ Google Ads endpoint
python test_google_ads.py  # (ถ้ามี)
```

### Test Docker Build:

```bash
# Build Docker image
docker build -t python-api .

# Run container
docker run -p 5000:5000 --env-file python-api/.env python-api

# Test API
curl http://localhost:5000/health
```

## 📦 Railway Deployment

### การ Deploy:

1. **Push code ไป GitHub:**

   ```bash
   git add .
   git commit -m "Fix Docker build and update dependencies"
   git push origin main
   ```

2. **Railway จะ auto-deploy** โดยใช้ Dockerfile ใหม่

3. **ตรวจสอบ logs** ใน Railway dashboard:
   - ดู build logs
   - ตรวจสอบว่า pip install สำเร็จ
   - ดู deployment logs

### Environment Variables (Railway):

ตรวจสอบว่ามี variables เหล่านี้:

```env
# Google Sheets
GOOGLE_SPREADSHEET_ID=...
GOOGLE_SERVICE_ACCOUNT_EMAIL=...
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY=...

# Facebook Ads
FACEBOOK_ACCESS_TOKEN=...
FACEBOOK_AD_ACCOUNT_ID=...

# Google Ads
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=...

# Database
DATABASE_URL=...

# Flask
FLASK_ENV=production
PORT=5000
```

## 🎯 สิ่งที่ได้แก้ไข

- ✅ แก้ปัญหา timeout ในการ download packages
- ✅ แก้ปัญหา dependency conflict ของ grpcio
- ✅ อัปเดต Google Ads API ให้ใช้ version ล่าสุด
- ✅ ปรับปรุง Dockerfile ให้ robust ขึ้น
- ✅ สร้าง .dockerignore เพื่อ optimize build
- ✅ ทดสอบว่า API ยังทำงานปกติ

## 🔍 Expected Build Time

- **Before:** ~5-10 minutes (มี timeout)
- **After:** ~3-5 minutes (ไม่มี error)

## 🚨 Troubleshooting

### ถ้ายัง timeout:

1. **ตรวจสอบ network:** Railway อาจมีปัญหา network ชั่วคระ
2. **ลอง rebuild:** คลิก "Redeploy" ใน Railway
3. **ตรวจสอบ Railway status:** https://railway.app/status

### ถ้ามี dependency error:

1. **ตรวจสอบ versions:** ดูว่า versions ใน requirements.txt ถูกต้อง
2. **ล้าง cache:** `pip cache purge` แล้วติดตั้งใหม่
3. **ใช้ virtual environment:** สร้าง venv ใหม่เพื่อทดสอบ

## 📚 References

- [Google Ads Python Client](https://github.com/googleads/google-ads-python)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Railway Documentation](https://docs.railway.app/)
- [pip Timeout Issues](https://pip.pypa.io/en/stable/topics/configuration/)

## 📝 Notes

- Google Ads API v17 เป็น version ล่าสุดที่รองรับใน `google-ads==22.1.0`
- ควร update pip เป็น version ล่าสุดเสมอ: `pip install --upgrade pip`
- `.dockerignore` ช่วยลดเวลา build ลงได้มาก
