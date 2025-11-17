# คู่มือการเชื่อมต่อ PostgreSQL Database กับ Railway

## 🎯 ภาพรวม

เนื่องจาก Railway ไม่สามารถเชื่อมต่อกับ Private IP (192.168.1.19) ได้โดยตรง คุณมี 2 ตัวเลือกหลัก:

1. **ใช้ Public IP/Domain** - เปิด PostgreSQL ให้เข้าถึงจาก Internet
2. **ย้าย Database ไป Railway** - สร้าง PostgreSQL บน Railway (แนะนำ)

---

## ✅ วิธีที่ 1: เปิด PostgreSQL ให้เข้าถึงจาก Internet

### ขั้นตอนที่ 1: ตรวจสอบ Public IP ของคุณ

```bash
# เช็ค Public IP
curl ifconfig.me
```

### ขั้นตอนที่ 2: แก้ไขไฟล์ PostgreSQL Configuration

**ไฟล์: `postgresql.conf`**

```conf
# เปลี่ยนจาก localhost เป็น 0.0.0.0
listen_addresses = '*'
port = 5432
```

**ไฟล์: `pg_hba.conf`**

```conf
# เพิ่มบรรทัดนี้เพื่ออนุญาตการเชื่อมต่อจากภายนอก
host    all             all             0.0.0.0/0               md5
```

### ขั้นตอนที่ 3: Restart PostgreSQL

```bash
# สำหรับ Linux
sudo systemctl restart postgresql

# สำหรับ Windows (ใน Services)
# หรือรันคำสั่งใน cmd
net stop postgresql-x64-16
net start postgresql-x64-16
```

### ขั้นตอนที่ 4: เปิด Firewall

```bash
# Linux - UFW
sudo ufw allow 5432/tcp

# Windows Firewall
# Control Panel > Windows Defender Firewall > Advanced Settings
# Inbound Rules > New Rule > Port > TCP 5432 > Allow
```

### ขั้นตอนที่ 5: Port Forwarding บน Router

1. เข้า Router Admin Panel (เช่น 192.168.1.1)
2. หา Port Forwarding หรือ Virtual Server
3. เพิ่ม Rule:
   - **External Port:** 5432
   - **Internal IP:** 192.168.1.19
   - **Internal Port:** 5432
   - **Protocol:** TCP

### ขั้นตอนที่ 6: อัพเดท Railway Environment Variables

```bash
DB_HOST=<YOUR_PUBLIC_IP>  # เช่น 1.2.3.4
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Bjh12345!!
DB_NAME=postgres
```

⚠️ **คำเตือน:** วิธีนี้มีความเสี่ยงด้านความปลอดภัย ควรใช้ Strong Password และ Whitelist IP

---

## ✅ วิธีที่ 2: ย้าย Database ไป Railway (แนะนำ ⭐)

### ขั้นตอนที่ 1: สร้าง PostgreSQL บน Railway

1. เข้า **Railway Dashboard**: https://railway.app
2. เลือก Project: **believable-ambition-production**
3. คลิก **+ New**
4. เลือก **Database** → **PostgreSQL**
5. รอให้ Railway สร้าง Database (ประมาณ 1-2 นาที)

### ขั้นตอนที่ 2: คัดลอกข้อมูลการเชื่อมต่อ

ไปที่ PostgreSQL Service ที่สร้างใหม่ → **Variables** tab

คัดลอกค่าเหล่านี้:

```
PGHOST=xxxx.railway.app
PGPORT=xxxx
PGUSER=postgres
PGPASSWORD=xxxxxxxxxxxx
PGDATABASE=railway
```

### ขั้นตอนที่ 3: Export ข้อมูลจาก Local PostgreSQL

**ใช้ Command Line:**

```bash
# Windows (PowerShell)
pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres --schema="BJH-Server" --table=bjh_all_leads -f bjh_backup.sql

# ป้อน Password เมื่อถูกถาม: Bjh12345!!
```

**หรือใช้ pgAdmin:**

1. เปิด pgAdmin
2. เชื่อมต่อกับ 192.168.1.19
3. ขวาคลิกที่ Table `bjh_all_leads` → **Backup**
4. Format: **Plain**
5. Save เป็น `bjh_backup.sql`

### ขั้นตอนที่ 4: Import ข้อมูลไป Railway PostgreSQL

**วิธีที่ 1: ใช้ Command Line**

```bash
# สร้าง Schema ก่อน (ถ้ายังไม่มี)
psql -h <RAILWAY_PGHOST> -p <RAILWAY_PGPORT> -U postgres -d railway -c 'CREATE SCHEMA IF NOT EXISTS "BJH-Server"'

# Import ข้อมูล
psql -h <RAILWAY_PGHOST> -p <RAILWAY_PGPORT> -U postgres -d railway -f bjh_backup.sql
```

**วิธีที่ 2: ใช้ pgAdmin**

1. เปิด pgAdmin
2. **Add New Server:**
   - **Name:** Railway PostgreSQL
   - **Host:** `<RAILWAY_PGHOST>`
   - **Port:** `<RAILWAY_PGPORT>`
   - **Username:** `postgres`
   - **Password:** `<RAILWAY_PGPASSWORD>`
   - **Database:** `railway`
3. เชื่อมต่อสำเร็จแล้ว → ขวาคลิกที่ Database → **Restore**
4. เลือกไฟล์ `bjh_backup.sql`
5. กด **Restore**

**วิธีที่ 3: ใช้ DBeaver (แนะนำ)**

1. ดาวน์โหลด DBeaver: https://dbeaver.io
2. สร้าง Connection ไปยัง Railway PostgreSQL
3. เปิด SQL Editor → เปิดไฟล์ `bjh_backup.sql`
4. กด **Execute**

### ขั้นตอนที่ 5: ตรวจสอบข้อมูล

```sql
-- ตรวจสอบว่ามี Schema
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'BJH-Server';

-- ตรวจสอบว่ามี Table
SELECT * FROM information_schema.tables WHERE table_schema = 'BJH-Server' AND table_name = 'bjh_all_leads';

-- นับจำนวนข้อมูล
SELECT COUNT(*) FROM "BJH-Server"."bjh_all_leads";
```

### ขั้นตอนที่ 6: อัพเดท Environment Variables ใน Railway API Service

1. ไปที่ Service **believable-ambition-production** (API service)
2. ไปที่ **Variables** tab
3. อัพเดทค่าต่อไปนี้:

```bash
DB_HOST=<RAILWAY_PGHOST>
DB_PORT=<RAILWAY_PGPORT>
DB_USER=postgres
DB_PASSWORD=<RAILWAY_PGPASSWORD>
DB_NAME=railway
```

4. กด **Deploy** (Railway จะ deploy อัตโนมัติ)

### ขั้นตอนที่ 7: ทดสอบ API

```bash
# ทดสอบ API endpoint
curl https://believable-ambition-production.up.railway.app/data_bjh?limit=10
```

หรือเปิดใน Browser:

```
https://believable-ambition-production.up.railway.app/data_bjh
```

---

## 🔍 Troubleshooting

### ปัญหา: Connection Timeout

**สาเหตุ:** Railway ไม่สามารถเชื่อมต่อกับ Database

**วิธีแก้:**

1. ตรวจสอบว่า `DB_HOST` ไม่ใช่ Private IP (192.168.x.x)
2. ตรวจสอบว่า Credentials ถูกต้อง
3. ดู Railway Logs: คลิก Service → **Deployments** → คลิกที่ Latest Deployment → ดู Logs

### ปัญหา: Table Not Found

**สาเหตุ:** Schema หรือ Table ยังไม่ถูกสร้าง

**วิธีแก้:**

```sql
-- สร้าง Schema
CREATE SCHEMA IF NOT EXISTS "BJH-Server";

-- ตรวจสอบ Schema และ Table
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
```

### ปัญหา: Authentication Failed

**สาเหตุ:** Password ไม่ถูกต้องหรือมีอักขระพิเศษ

**วิธีแก้:**

- ตรวจสอบว่า Password ครบถ้วน
- ถ้า Password มี `!` ต้อง escape: `\!`
- หรือใส่ double quotes: `"Bjh12345!!"`

### ปัญหา: Too Many Connections

**สาเหตุ:** Connection Pool เต็ม

**วิธีแก้:** เพิ่ม Connection Pooling ใน `db_connection.py`:

```python
import psycopg2.pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min=1, max=20
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
```

---

## 📊 เปรียบเทียบ

|                   | วิธีที่ 1: Public IP    | วิธีที่ 2: Railway PostgreSQL |
| ----------------- | ----------------------- | ----------------------------- |
| **ความยาก**       | ปานกลาง                 | ง่าย                          |
| **ความปลอดภัย**   | ต่ำ (ต้องเปิด Internet) | สูง (Internal Network)        |
| **ค่าใช้จ่าย**    | ฟรี (ใช้ Server เดิม)   | ฟรี (ใช้ Free Tier)           |
| **Performance**   | ขึ้นอยู่กับ Internet    | เร็ว (Same Network)           |
| **การบำรุงรักษา** | ต้องดูแล Server เอง     | Railway ดูแลให้               |
| **แนะนำ**         | ❌ ไม่แนะนำ             | ✅ แนะนำ                      |

---

## 🎯 สรุป

**แนะนำให้ใช้วิธีที่ 2** - ย้าย Database ไป Railway เพราะ:

- ✅ ปลอดภัยกว่า
- ✅ ไม่ต้องเปิด Port ที่ Local
- ✅ Performance ดีกว่า (Same Data Center)
- ✅ Backup และ Scale ง่าย
- ✅ Free Tier ใช้ได้สบาย

**ขั้นตอนย่อ:**

1. สร้าง PostgreSQL บน Railway
2. Export ข้อมูลด้วย `pg_dump`
3. Import ด้วย `psql` หรือ pgAdmin
4. อัพเดท Environment Variables
5. Deploy และทดสอบ

---

## 📞 ต้องการความช่วยเหลือ?

หากมีปัญหาในการ setup ติดต่อได้ที่:

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
