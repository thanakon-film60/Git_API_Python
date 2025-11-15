# 🚀 Google Ads API Setup Guide

คู่มือการตั้งค่า Google Ads API สำหรับ Dashboard

---

## 📋 สิ่งที่ต้องเตรียม

✅ บัญชี Google Ads ที่ใช้งานอยู่  
✅ Google Cloud Project  
✅ OAuth 2.0 Credentials  
✅ Node.js ติดตั้งในเครื่อง

---

## 🔧 ขั้นตอนที่ 1: สร้าง Google Cloud Project

### 1.1 สร้าง Project ใหม่

1. ไปที่ https://console.cloud.google.com
2. คลิก **Select a project** → **New Project**
3. ตั้งชื่อ: `TPP Ads Dashboard`
4. คลิก **Create**

### 1.2 เปิดใช้งาน Google Ads API

1. ไปที่ **APIs & Services** → **Library**
2. ค้นหา: `Google Ads API`
3. คลิก **Enable**

### 1.3 สร้าง OAuth 2.0 Credentials

1. ไปที่ **APIs & Services** → **Credentials**
2. คลิก **Create Credentials** → **OAuth client ID**
3. เลือก Application type: **Web application**
4. ตั้งชื่อ: `TPP Ads API Client`
5. **Authorized redirect URIs**: เพิ่ม `http://localhost:3000/oauth2callback`
6. คลิก **Create**
7. **คัดลอก Client ID และ Client Secret เก็บไว้**

---

## 🔑 ขั้นตอนที่ 2: Generate Refresh Token

### 2.1 ติดตั้ง Dependencies

```bash
cd scripts
npm install google-auth-library readline
```

### 2.2 แก้ไขไฟล์ Script

เปิดไฟล์ `scripts/generate-google-ads-refresh-token.js` และแก้ไข:

```javascript
const CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com";
const CLIENT_SECRET = "YOUR_CLIENT_SECRET";
```

ใส่ Client ID และ Client Secret ที่ได้จากขั้นตอนที่ 1.3

### 2.3 รัน Script

```bash
node scripts/generate-google-ads-refresh-token.js
```

### 2.4 ทำตามขั้นตอน

1. Script จะแสดง URL → **คัดลอกและเปิดในเบราว์เซอร์**
2. Login ด้วย Google Account ที่มีสิทธิ์เข้าถึง Google Ads
3. อนุญาตการเข้าถึง
4. เบราว์เซอร์จะ redirect ไปที่ URL ที่มี `code=...` → **คัดลอก code**
5. วาง code ใน terminal
6. จะได้ **Refresh Token** → **เก็บไว้**

---

## 🎯 ขั้นตอนที่ 3: หา Customer ID

### 3.1 เข้า Google Ads

1. ไปที่ https://ads.google.com
2. Login เข้าบัญชี Google Ads

### 3.2 หา Customer ID

- ดูที่ **มุมบนขวา** จะเห็นรหัสรูปแบบ: `123-456-7890`
- **บันทึกเลขนี้โดยไม่มีขีด** เช่น: `1234567890`

### 3.3 ระวัง Manager Account vs Client Account

- **Manager Account (MCC)**: ใช้จัดการหลาย account (ไม่สามารถใช้ใน API ได้)
- **Client Account**: บัญชีโฆษณาจริง ✅ **ใช้อันนี้**

ถ้าคุณมี Manager Account ให้:

1. คลิกที่ชื่อ account มุมบนซ้าย
2. เลือก **Client Account** ที่ต้องการ
3. คัดลอก Customer ID ของ Client Account

---

## 🔐 ขั้นตอนที่ 4: ขอ Developer Token

### 4.1 สมัครขอ API Access

1. ไปที่ https://ads.google.com
2. คลิก **Tools & Settings** (ไอคอนประแจที่มุมบนขวา)
3. ไปที่ **Setup** → **API Center**
4. คลิก **Apply for access** หรือ **Request API access**

### 4.2 กรอกแบบฟอร์ม

- **Application name**: `TPP Ads Dashboard`
- **Purpose**: `For internal dashboard and reporting`
- **API usage**: `Read-only data for analytics and reporting`

### 4.3 Submit

- คลิก **Submit**
- **รออนุมัติ 1-3 วันทำการ**

### 4.4 ใช้ Test Mode ก่อน (ถ้าต้องการทดสอบก่อน)

- Google จะให้ **Test Access** ใช้ได้ทันที
- ข้อจำกัด: 15,000 operations/day
- ได้ Developer Token ชั่วคราวมาใช้ก่อน

---

## 🎉 ขั้นตอนที่ 5: ตั้งค่า Environment Variables

เมื่อได้ข้อมูลครบแล้ว เพิ่มใน `.env`:

```env
# Google Ads API
GOOGLE_ADS_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=YOUR_CLIENT_SECRET
GOOGLE_ADS_DEVELOPER_TOKEN=YOUR_DEVELOPER_TOKEN
GOOGLE_ADS_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

---

## ✅ ทดสอบ API

### Local Test

```bash
python test_env.py
python app.py
```

เข้า:

```
http://localhost:5000/api/google-ads?startDate=2025-11-14&endDate=2025-11-14
```

### Railway Deploy

อัปเดต Environment Variables บน Railway Dashboard

---

## 🐛 Troubleshooting

### ❌ Error: "Invalid client"

- ตรวจสอบ Client ID และ Client Secret
- ตรวจสอบ Redirect URI ว่าตรงกับที่ตั้งค่าใน Google Cloud

### ❌ Error: "Invalid grant"

- Refresh Token อาจหมดอายุ → Generate ใหม่
- ตรวจสอบว่าใช้ Google Account ที่ถูกต้อง

### ❌ Error: "Developer token is invalid"

- รอการอนุมัติจาก Google
- หรือใช้ Test Access ก่อน

### ❌ Error: "Customer ID not found"

- ตรวจสอบว่าใช้ Client Account ไม่ใช่ Manager Account
- ลบขีด `-` ออกจาก Customer ID

---

## 📚 Resources

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [OAuth 2.0 Setup](https://developers.google.com/google-ads/api/docs/oauth/overview)
- [API Access Levels](https://developers.google.com/google-ads/api/docs/access-levels)

---

## 📞 Need Help?

ถ้าติ���ปัญหาตรงไหน สามารถดูเพิ่มเติมได้ที่:

- Google Ads API Forum: https://groups.google.com/g/adwords-api
- Stack Overflow: `[google-ads-api]` tag

---

**สร้างเมื่อ:** 14 พฤศจิกายน 2025  
**สำหรับ:** TPP Ads Dashboard
