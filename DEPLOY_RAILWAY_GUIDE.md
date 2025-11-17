# 🚀 คู่มือ Deploy API ขึ้น Railway

## 📋 สิ่งที่ต้องเตรียม

### 1. ไฟล์ที่จำเป็น (มีครบแล้ว ✅)

- ✅ `Dockerfile` - สำหรับ build Docker image
- ✅ `railway.json` - config สำหรับ Railway
- ✅ `python-api/requirements.txt` - Python dependencies
- ✅ `python-api/Procfile` - กำหนดคำสั่งรัน web server
- ✅ `python-api/app.py` - Flask API
- ✅ `python-api/db_connection.py` - Database connection

---

## 🎯 ขั้นตอนการ Deploy

### Step 1: สร้าง Project บน Railway

1. ไปที่ https://railway.app
2. Login ด้วย GitHub account
3. คลิก **New Project**
4. เลือก **Deploy from GitHub repo**
5. เลือก repository: `Git_API_Python`
6. Railway จะเริ่ม deploy อัตโนมัติ

---

### Step 2: ⚠️ แก้ปัญหา Database Connection (สำคัญมาก!)

**ปัญหา:** Railway ไม่สามารถเชื่อมต่อกับ Local IP (192.168.1.19) ได้

**วิธีแก้ที่แนะนำ 3 วิธี:**

#### 🔥 วิธีที่ 1: ใช้ Railway PostgreSQL (แนะนำ - ฟรี 500 ชั่วโมง/เดือน)

**สร้าง PostgreSQL Database:**

1. ใน Railway Project คลิก **+ New**
2. เลือก **Database** → **PostgreSQL**
3. Railway จะสร้าง PostgreSQL ให้อัตโนมัติ

**คัดลอกข้อมูล Database:**

1. คลิกที่ PostgreSQL service ที่สร้าง
2. ไปที่ tab **Variables**
3. คัดลอกค่าเหล่านี้:
   - `PGHOST`
   - `PGPORT` (5432)
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`

**Import ข้อมูลจาก Local → Railway:**

```bash
# 1. Export ข้อมูลจาก Local PostgreSQL
pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres \
  --schema="BJH-Server" \
  --table=bjh_all_leads \
  -f bjh_backup.sql

# 2. Import ไป Railway PostgreSQL
psql -h <RAILWAY_PGHOST> \
     -p <RAILWAY_PGPORT> \
     -U <RAILWAY_PGUSER> \
     -d <RAILWAY_PGDATABASE> \
     -f bjh_backup.sql
```

**หรือใช้ GUI Tools:**

- **pgAdmin**: Import/Export data
- **DBeaver**: Database migration
- **TablePlus**: Simple data transfer

---

#### 🌐 วิธีที่ 2: ใช้ Supabase (แนะนำ - ฟรีตลอด)

**ขั้นตอน:**

1. สร้าง Project ที่ https://supabase.com
2. คลิก **Settings** → **Database**
3. คัดลอก Connection String
4. Import ข้อมูลผ่าน SQL Editor ใน Supabase Dashboard

**Connection Info:**

```
Host: db.xxxxxxxxxxxxx.supabase.co
Port: 5432
Database: postgres
User: postgres
Password: [your-password]
```

---

#### 🐳 วิธีที่ 3: ใช้ PostgreSQL บน n8n.bjhbangkok.com (แนะนำ - มี Docker แล้ว!)

**ข้อดี:**

- Server มี Docker อยู่แล้ว
- มี domain name (n8n.bjhbangkok.com)
- ควบคุมได้เต็มที่
- ไม่มีค่าใช้จ่ายเพิ่มเติม

**ขั้นตอน:**

1. **SSH เข้า n8n.bjhbangkok.com:**

   ```bash
   ssh user@n8n.bjhbangkok.com
   ```

2. **รัน PostgreSQL ด้วย Docker:**

   ```bash
   # สร้าง volume สำหรับเก็บข้อมูล
   docker volume create postgres_data

   # รัน PostgreSQL container
   docker run -d \
     --name bjh_postgres \
     --restart always \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=Bjh12345!! \
     -e POSTGRES_DB=postgres \
     -p 5432:5432 \
     -v postgres_data:/var/lib/postgresql/data \
     postgres:15-alpine
   ```

3. **ตรวจสอบว่า PostgreSQL ทำงาน:**

   ```bash
   docker ps | grep bjh_postgres
   docker logs bjh_postgres
   ```

4. **สร้าง Schema และ Table:**

   ```bash
   # เข้าไปใน container
   docker exec -it bjh_postgres psql -U postgres

   # สร้าง schema
   CREATE SCHEMA "BJH-Server";

   # สร้าง table (ตัวอย่าง)
   CREATE TABLE "BJH-Server".bjh_all_leads (
     id SERIAL PRIMARY KEY,
     name VARCHAR(255),
     phone VARCHAR(20),
     status VARCHAR(50),
     source VARCHAR(100),
     doctor VARCHAR(100),
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   # ออกจาก psql
   \q
   ```

5. **Import ข้อมูลจาก Local (192.168.1.19):**

   **ถ้ามีข้อมูลอยู่แล้ว:**

   ```bash
   # บน Local machine (192.168.1.19)
   pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres \
     --schema="BJH-Server" \
     -f bjh_backup.sql

   # คัดลอกไปยัง server
   scp bjh_backup.sql user@n8n.bjhbangkok.com:/tmp/

   # บน n8n.bjhbangkok.com
   docker exec -i bjh_postgres psql -U postgres < /tmp/bjh_backup.sql
   ```

6. **เปิด Firewall Port 5432:**

   ```bash
   # Ubuntu/Debian
   sudo ufw allow 5432/tcp

   # หรือใช้ iptables
   sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT
   ```

7. **ตั้งค่า PostgreSQL ให้รับ connection จากภายนอก:**

   ```bash
   # แก้ไข postgresql.conf
   docker exec -it bjh_postgres bash
   echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf

   # แก้ไข pg_hba.conf
   echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf

   exit

   # Restart container
   docker restart bjh_postgres
   ```

8. **ทดสอบการเชื่อมต่อจากภายนอก:**

   ```bash
   # จาก Local machine
   psql -h n8n.bjhbangkok.com -p 5432 -U postgres -d postgres
   ```

9. **ตั้งค่าใน Railway Environment Variables:**
   ```env
   DB_HOST=n8n.bjhbangkok.com
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=Bjh12345!!
   DB_NAME=postgres
   ```

**💡 เคล็ดลับความปลอดภัย:**

- ใช้ SSL/TLS สำหรับ connection
- จำกัด IP ที่สามารถเข้าถึง (Whitelist Railway IP)
- เปลี่ยน password ที่แข็งแรงกว่า
- ใช้ non-default port ถ้าเป็นไปได้

**🔒 ตั้งค่า SSL (แนะนำ):**

```bash
# Generate self-signed certificate
docker exec -it bjh_postgres bash
cd /var/lib/postgresql/data
openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key
chmod 600 server.key
chown postgres:postgres server.key server.crt
exit

docker restart bjh_postgres
```

---

### Step 3: ตั้งค่า Environment Variables

1. ใน Railway Project → คลิกที่ **Variables**
2. เพิ่มตัวแปรเหล่านี้:

```env
# Database Configuration (ใช้ข้อมูลจาก Railway PostgreSQL หรือ Supabase)
DB_HOST=n8n.bjhbangkok.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Bjh12345!!
DB_NAME=postgres

# Facebook Ads API
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBP5kZBuQfpSzBZATCVdS1poTSVJasZCZBlB3RrCKN3fJ6NMAn8GdOONsoX7Awf1yNjZAlUAs6SNdnsfGnwzrFCQkzGDUQb3tK86NKHZAzed1XugUuYyV5gxPyIZBYJS996bXzfW1wVmdjgUxsOJoFUF8tykzoeF3BSXmUcNYZBkF7ZCwRBtxdpsAvKFNQ9
FACEBOOK_AD_ACCOUNT_ID=act_454323590676166

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SHEET_ID=1OdHZNSlS-SrUpn4wIEn_6tegeVkv3spBfj-FyRRxg3Y
GOOGLE_SERVICE_ACCOUNT_EMAIL=web-sheets-reader@name-tel-dev.iam.gserviceaccount.com
GOOGLE_PROJECT_ID=name-tel-dev

# Google Service Account Private Key (ใส่ทั้งหมดรวม -----BEGIN และ END-----)
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

# Google Ads API
GOOGLE_ADS_CLIENT_ID=310364673147-1tbnkgujso2smo0t0qsqjd95n9oorbe9.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=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
GOOGLE_ADS_DEVELOPER_TOKEN=8KWFw-bsGe920_kfcQuT_g
GOOGLE_ADS_REFRESH_TOKEN=1//0guXuiYplyga8CgYIARAAGBASNwF-L9Ir8tKM-AjQ5EVTjDy0GvYh8kDNeTqZ1kWx_VbgvygQ6ueh4grcQ0LwI201x5t87uK7YkA
GOOGLE_ADS_CUSTOMER_ID=4275609411

# Flask Configuration
FLASK_ENV=production
PORT=5000
CACHE_DURATION=30
```

**💡 เคล็ดลับ:**

- ใช้ **Raw Editor** ใน Railway สะดวกกว่า (คัดลอก-วางได้ทั้งหมด)
- Private Key ต้องใส่ใน `"..."` และมี `\n` แทน line break
- ตรวจสอบให้แน่ใจว่าไม่มีช่องว่างหรือ special characters ผิด

---

### Step 4: ตรวจสอบการ Deploy

1. **ดู Build Logs:**

   - ใน Railway Dashboard → คลิก **Deployments**
   - ดูว่า Build สำเร็จหรือไม่

2. **ดู Runtime Logs:**

   - คลิกที่ Active Deployment
   - ตรวจสอบ error messages
   - ดูว่าเชื่อมต่อ Database สำเร็จหรือไม่

3. **Test API:**
   ```bash
   # เปลี่ยน YOUR_APP_URL เป็น URL ของคุณ
   curl https://YOUR_APP_URL.up.railway.app/health
   curl https://YOUR_APP_URL.up.railway.app/data_bjh
   ```

---

### Step 5: ตั้งค่า Custom Domain (ถ้าต้องการ)

1. ใน Railway Project → คลิก **Settings**
2. ไปที่ส่วน **Domains**
3. คลิก **Generate Domain** (Railway จะให้ domain ฟรี)
4. หรือเพิ่ม Custom Domain ของคุณเอง

**Domain แบบฟรีจาก Railway:**

- `your-app-name.up.railway.app`

---

## 📊 API Endpoints ที่พร้อมใช้

Base URL: `https://YOUR_APP_URL.up.railway.app`

### Database Endpoints

- `GET /data_bjh` - ดึงข้อมูล leads ทั้งหมด
- `GET /data_bjh?limit=100` - จำกัดจำนวน
- `GET /data_bjh?status=active` - กรองตาม status
- `GET /data_bjh?source=Facebook` - กรองตาม source

### Google Sheets Endpoints

- `GET /film-data` - ข้อมูล Film data sheet
- `GET /run-time` - สถิติการโทร
- `GET /N_SaleIncentive_data` - ข้อมูล Sale Incentive

### Ads Endpoints

- `GET /api/facebook-ads-campaigns` - Facebook Ads data
- `GET /api/google-ads` - Google Ads data

---

## 🔧 Troubleshooting

### ❌ ปัญหา: Connection timed out

```
could not connect to server: Connection timed out
Is the server running on host "192.168.1.19" and accepting TCP/IP connections?
```

**วิธีแก้:** Railway ไม่สามารถเข้าถึง Private IP ได้ → ใช้วิธีที่ 1 หรือ 2 ข้างต้น

---

### ❌ ปัญหา: Build Failed

**ตรวจสอบ:**

1. `requirements.txt` มี dependencies ครบหรือไม่
2. `Dockerfile` ถูกต้องหรือไม่
3. Python version รองรับหรือไม่

---

### ❌ ปัญหา: Application Error

**ตรวจสอบ:**

1. Environment Variables ครบหรือไม่
2. ตรวจสอบ Logs มี error message อะไร
3. ทดสอบ API endpoints ทีละตัว

---

### ❌ ปัญหา: Google Sheets API Error

```
Error: Missing Google credentials in environment variables
```

**วิธีแก้:**

1. ตรวจสอบว่าตั้งค่า `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY` ถูกต้อง
2. Private Key ต้องมี `"..."` ครอบ
3. ลอง regenerate Service Account Key ใหม่

---

## 💰 ค่าใช้จ่าย Railway

### Free Plan (Hobby):

- 500 ชั่วโมงการใช้งาน/เดือน (ประมาณ 20 วัน)
- $5 credit ต่อเดือน
- Shared resources
- **เหมาะสำหรับ:** Development, Testing

### Pro Plan ($20/เดือน):

- Unlimited execution time
- Priority support
- More resources
- **เหมาะสำหรับ:** Production

**💡 เคล็ดลับประหยัดค่าใช้จ่าย:**

- ใช้ Sleep Mode (Railway จะหยุด service เมื่อไม่มีการใช้งาน)
- Monitor usage ใน Dashboard
- ใช้ PostgreSQL จาก Supabase (ฟรี) แทน Railway PostgreSQL

---

## 📚 เอกสารเพิ่มเติม

- [Railway Documentation](https://docs.railway.app/)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)
- [Deploy Flask Apps](https://docs.railway.app/guides/flask)
- [Environment Variables](https://docs.railway.app/develop/variables)

---

## ✅ Checklist ก่อน Deploy

- [ ] ตรวจสอบ `requirements.txt` มี dependencies ครบ
- [ ] ตรวจสอบ `Dockerfile` และ `railway.json` ถูกต้อง
- [ ] เตรียม Database (Railway PostgreSQL หรือ Supabase)
- [ ] คัดลอก Environment Variables ทั้งหมด
- [ ] Import ข้อมูลจาก Local → Cloud Database
- [ ] ทดสอบการเชื่อมต่อ Database
- [ ] Deploy และตรวจสอบ Logs
- [ ] Test API endpoints ทั้งหมด
- [ ] ตั้งค่า Custom Domain (ถ้าต้องการ)

---

## 🎉 สำเร็จ!

เมื่อ Deploy สำเร็จ API จะพร้อมใช้งานที่:

```
https://YOUR_APP_URL.up.railway.app
```

ทดสอบด้วย:

```bash
curl https://YOUR_APP_URL.up.railway.app/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T...",
  "cache_status": {...}
}
```
