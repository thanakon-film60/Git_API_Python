# Railway Setup Guide สำหรับ PostgreSQL API

## ขั้นตอนการตั้งค่า Environment Variables บน Railway

### 1. เข้าสู่ Railway Dashboard

ไปที่: https://railway.app/project/your-project

### 2. ตั้งค่า Environment Variables

ใน Railway Dashboard > Variables > Raw Editor:

```
DB_HOST=192.168.1.19
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Bjh12345!!
DB_NAME=postgres
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBP5kZBuQfpSzBZATCVdS1poTSVJasZCZBlB3RrCKN3fJ6NMAn8GdOONsoX7Awf1yNjZAlUAs6SNdnsfGnwzrFCQkzGDUQb3tK86NKHZAzed1XugUuYyV5gxPyIZBYJS996bXzfW1wVmdjgUxsOJoFUF8tykzoeF3BSXmUcNYZBkF7ZCwRBtxdpsAvKFNQ9
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166
GOOGLE_SPREADSHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SERVICE_ACCOUNT_EMAIL=web-sheets-reader@name-tel-dev.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCZ97WjLIORTUMU
pAh6tEiL9iktiTN8TbwdlAO3lin58vAIMkeAqYxTswV+ewS4Uw3wgABZZyDREfKG
iX9er5C3MYQm08g6J8ZUbuYDVHL2aPcxJ2lfG7XzOTOeq7QhSxTZwLVAf4RAdV0m
bPyZHDToFoUwNgrXqys6/66eE3MocbN+RHLxHTO22ufKiRUN0gk3wYbYq5LDmT+f
OyfrViuTFWcnAnMHtHjfIPNsnpYXNqXOkpOFY2PvgGntcwoZKB/Eud4mYW8e0Dn1
oe5C+KEcljrxsianyfkRZRv17rW9xwu9kQ0RzqkZsuL7Ga8L22FrIrPmnx24Huns
25wtioC/AgMBAAECggEABTHBM/8VdTp5D+I00wbwB6DHZNzjGsd4mDrdIT10rxUO
GgiwNtwBevVoMwstbpaGut1mpZ2AEu2bFAThgi1EIZoPDkxIzgV3gHO5WNVph3yl
Ekh1GptRuSHt5uV+Dz18N5hzxPhIWvBasygsIXI9KrNPzP+VwA7rR3NGzdh0IyId
c7MVDTMA3exlLAeEfMzOoAwVz2a6jYueHs4pXAJqTg/dCTOqOwR6DqQJKn93jrwz
advMDrQFe7JQbfzAti5RcPvxA8n7qTsprpEZGZ4oYfKcNRumKQPxQpuBA7I+s/LC
BpmbCb5HJllLHuPxnDHNkxUYDgzhMobikpmjTFQqOQKBgQDSr/6Tz2wq4j1vdQob
xssxljEZGZY6M+NUUa8yny/6qQyHBwgAFBp1I4gj2Kd8l9yphMUAggzBf05m77sO
0MeUmBCRZx/GnN6FHQ48IhIynBMGcNEL1E59jWhscnnod4rwUUf9cG6IT5vvyXLG
i5a2i8e9ZxaftHvhWQIbMUtFdQKBgQC7FNb6ij0gV+J3eWzZ+pMfyCdtsKnnLSh4
DFPIlbLVRfK/0Dy+XTstoh0PMqH9zS/SmVKe4YUojLOtCz6O6njm9OyvxjQs0yEw
MCK6f3dk4TGPFGfY3h9m15xlgP6nvNxbLc3odGoZEzbaKcVq285cuycw8+eF1yp9
dsNmlx0C4wKBgHPQDJfBqEr2bCDtbC4Sm7VZQwnyF7NMvISoFi80dBJMhLdgtRQd
+OE1M+vId2C0tbZ1Zjk+Q7bFvRo2Y1PkjiDvagQTdNMffe4cJ6wEao5pXsfmkfL3
tGGtrp4WW07fD3/EnlcBS7EgWa54xN/A8YrM0XIazcPiWUppPBAoi6DVAoGAGZdn
NQyWAgejph5JIqRhXdaediXViBcoUwu0plq8BOq1o0GUHaJZRwvHF94gRLy9zvxE
ThGhioN8zK4eF6TBdy6H9h+R4ZPcFWBwT7zCE12uztjGv+bautHBxizYKQ/vwNVK
NoM+REHZngxawhxhZVQAr3Sd9jQRzunhHvaK9GsCgYANcQ/IJJgWR8DcaMRTG5Zx
ez2xeda/4GXQ5pq2R0DTSfW985s/f1/4ms0FOsJHB8SrXPobyOgQBJVP1Lg2faUW
CHkHcDaQUJnGo8/i0+g6QOQJcBKaoPzeyiNSkg4/u55rXKagPtNWOyl9VCUNYbmJ
fPCvcFPqJVxMt92O5J3B7Q==
-----END PRIVATE KEY-----"
GOOGLE_PROJECT_ID=name-tel-dev
GOOGLE_ADS_CLIENT_ID=310364673147-1tbnkgujso2smo0t0qsqjd95n9oorbe9.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=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
GOOGLE_ADS_DEVELOPER_TOKEN=8KWFw-bsGe920_kfcQuT_g
GOOGLE_ADS_REFRESH_TOKEN=1//0guXuiYplyga8CgYIARAAGBASNwF-L9Ir8tKM-AjQ5EVTjDy0GvYh8kDNeTqZ1kWx_VbgvygQ6ueh4grcQ0LwI201x5t87uK7YkA
GOOGLE_ADS_CUSTOMER_ID=4275609411
FLASK_ENV=production
PORT=5000
CACHE_DURATION=30
```

### 3. สำคัญ! เกี่ยวกับ Database Connection

⚠️ **Railway ไม่สามารถเชื่อมต่อกับ Private IP (192.168.1.19) ได้**

**วิธีแก้ไข:**

#### ตัวเลือกที่ 1: ใช้ Public IP หรือ Domain

- ทำให้ PostgreSQL Server สามารถเข้าถึงได้จาก Internet
- ใช้ Public IP แทน 192.168.1.19
- หรือตั้ง Domain Name ให้กับ Database Server

#### ตัวเลือกที่ 2: Deploy PostgreSQL บน Railway (แนะนำ)

**ขั้นตอน:**

1. ไปที่ Railway Dashboard → เลือก Project **believable-ambition-production**
2. คลิก **+ New** → เลือก **Database** → เลือก **PostgreSQL**
3. Railway จะสร้าง PostgreSQL Database ให้อัตโนมัติ
4. ไปที่ **Variables** tab ของ PostgreSQL service ที่สร้างใหม่
5. คัดลอกค่าเหล่านี้:

   - `PGHOST` (hostname)
   - `PGPORT` (port)
   - `PGUSER` (username)
   - `PGPASSWORD` (password)
   - `PGDATABASE` (database name)

6. ไปที่ Service **believable-ambition-production** (API service)
7. อัพเดท Environment Variables:

   ```
   DB_HOST=<PGHOST จาก PostgreSQL service>
   DB_PORT=<PGPORT จาก PostgreSQL service>
   DB_USER=<PGUSER จาก PostgreSQL service>
   DB_PASSWORD=<PGPASSWORD จาก PostgreSQL service>
   DB_NAME=<PGDATABASE จาก PostgreSQL service>
   ```

8. **Import ข้อมูลจาก Local PostgreSQL ไป Railway PostgreSQL:**

   ```bash
   # Export ข้อมูลจาก Local
   pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres --schema="BJH-Server" --table=bjh_all_leads -f bjh_backup.sql

   # Import ไป Railway PostgreSQL
   psql -h <RAILWAY_PGHOST> -p <RAILWAY_PGPORT> -U <RAILWAY_PGUSER> -d <RAILWAY_PGDATABASE> -f bjh_backup.sql
   ```

   หรือใช้ GUI Tool เช่น pgAdmin, DBeaver

#### ตัวเลือกที่ 3: ใช้ External Database Service

- ใช้ Supabase (PostgreSQL hosting)
- ใช้ Neon (Serverless PostgreSQL)
- ใช้ Railway PostgreSQL

### 4. ตรวจสอบการ Deploy

หลังจากตั้งค่า Environment Variables แล้ว:

1. กด **Deploy** ใหม่
2. ตรวจสอบ Logs ว่าเชื่อมต่อ Database สำเร็จ
3. ทดสอบ API: `https://believable-ambition-production.up.railway.app/data_bjh`

### 5. API Endpoints

**Base URL:** `https://believable-ambition-production.up.railway.app`

- `GET /data_bjh` - ดึงข้อมูลทั้งหมด
- `GET /data_bjh?limit=10` - จำกัด 10 รายการ
- `GET /data_bjh?status=ไม่สนใจ` - กรองตาม status
- `GET /data_bjh?source=Facebook` - กรองตาม source
- `GET /data_bjh?phone=0988295616` - ค้นหาจากเบอร์โทร

### 6. Troubleshooting

**ถ้าเจอ Connection Error:**

```
could not connect to server: Connection timed out
```

แปลว่า Railway เชื่อมต่อกับ Private IP ไม่ได้ ต้องใช้วิธีข้างต้น

**ตรวจสอบ Logs:**

```bash
railway logs
```

---

## แนะนำ: ใช้ Supabase (ฟรี)

1. สร้าง Project ที่ https://supabase.com
2. คัดลอกข้อมูล Database
3. ตั้งค่าใน Railway:

```
DB_HOST=db.xxxxxxxxxxxxx.supabase.co
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-password
DB_NAME=postgres
```
