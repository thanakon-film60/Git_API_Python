# 🐳 Setup PostgreSQL บน n8n.bjhbangkok.com ด้วย Docker

## 🎯 คำสั่งเดียวจบ (Quick Setup)

```bash
# SSH เข้า server
ssh user@n8n.bjhbangkok.com

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

# เปิด firewall
sudo ufw allow 5432/tcp

# แก้ไขให้รับ connection จากภายนอก
docker exec -i bjh_postgres bash -c "echo \"listen_addresses = '*'\" >> /var/lib/postgresql/data/postgresql.conf"
docker exec -i bjh_postgres bash -c "echo \"host all all 0.0.0.0/0 md5\" >> /var/lib/postgresql/data/pg_hba.conf"

# Restart
docker restart bjh_postgres
```

---

## 📋 ขั้นตอนแบบละเอียด

### 1. SSH เข้า Server

```bash
ssh user@n8n.bjhbangkok.com
# หรือ
ssh user@192.168.1.19
```

---

### 2. ตรวจสอบ Docker

```bash
# ตรวจสอบว่ามี Docker แล้ว
docker --version

# ดู container ที่มีอยู่
docker ps -a
```

---

### 3. สร้าง PostgreSQL Container

```bash
# สร้าง Docker volume สำหรับเก็บข้อมูล (ไม่หายเวลา restart)
docker volume create postgres_data

# รัน PostgreSQL
docker run -d \
  --name bjh_postgres \
  --restart always \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=Bjh12345!! \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# อธิบาย:
# -d              : รันใน background
# --name          : ตั้งชื่อ container
# --restart       : restart อัตโนมัติเมื่อ server restart
# -e              : ตั้งค่า environment variables
# -p              : map port 5432 (host:container)
# -v              : mount volume สำหรับเก็บข้อมูล
# postgres:15-alpine : ใช้ PostgreSQL version 15 (Alpine = เบาและเร็ว)
```

---

### 4. ตรวจสอบสถานะ

```bash
# ดูว่า container ทำงานหรือไม่
docker ps | grep bjh_postgres

# ดู logs
docker logs bjh_postgres

# ดู logs แบบ real-time
docker logs -f bjh_postgres
```

---

### 5. สร้าง Schema และ Table

```bash
# เข้าไปใน PostgreSQL
docker exec -it bjh_postgres psql -U postgres

# สร้าง schema
CREATE SCHEMA "BJH-Server";

# เปลี่ยนไปใช้ schema
SET search_path TO "BJH-Server";

# สร้าง table (ปรับตามโครงสร้างจริง)
CREATE TABLE "BJH-Server".bjh_all_leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    status VARCHAR(50),
    source VARCHAR(100),
    doctor VARCHAR(100),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# สร้าง index เพื่อเพิ่มความเร็ว
CREATE INDEX idx_phone ON "BJH-Server".bjh_all_leads(phone);
CREATE INDEX idx_status ON "BJH-Server".bjh_all_leads(status);
CREATE INDEX idx_created_at ON "BJH-Server".bjh_all_leads(created_at);

# ตรวจสอบ table ที่สร้าง
\dt "BJH-Server".*

# ออกจาก psql
\q
```

---

### 6. Import ข้อมูลจาก Local Database (192.168.1.19)

#### วิธีที่ 1: Export/Import ทั้ง Schema

```bash
# บน Local machine (Windows)
# Export ข้อมูล
pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres ^
  --schema="BJH-Server" ^
  --format=custom ^
  -f bjh_backup.dump

# คัดลอกไปยัง server (ใช้ SCP หรือ WinSCP)
scp bjh_backup.dump user@n8n.bjhbangkok.com:/tmp/

# บน n8n.bjhbangkok.com
# Import ข้อมูล
docker exec -i bjh_postgres pg_restore -U postgres -d postgres /tmp/bjh_backup.dump
```

#### วิธีที่ 2: Export/Import เฉพาะ Table

```bash
# บน Local machine (Windows)
# Export เฉพาะ table bjh_all_leads
pg_dump -h 192.168.1.19 -p 5432 -U postgres -d postgres ^
  --schema="BJH-Server" ^
  --table=bjh_all_leads ^
  -f bjh_backup.sql

# คัดลอกไปยัง server
scp bjh_backup.sql user@n8n.bjhbangkok.com:/tmp/

# บน n8n.bjhbangkok.com
# Import
docker exec -i bjh_postgres psql -U postgres -d postgres < /tmp/bjh_backup.sql
```

#### วิธีที่ 3: ใช้ psql Copy (สำหรับข้อมูลเยอะ)

```bash
# Export ข้อมูลเป็น CSV
docker exec -i bjh_postgres psql -U postgres -d postgres -c \
  "COPY \"BJH-Server\".bjh_all_leads TO STDOUT WITH CSV HEADER" > data.csv

# Import CSV
docker exec -i bjh_postgres psql -U postgres -d postgres -c \
  "COPY \"BJH-Server\".bjh_all_leads FROM STDIN WITH CSV HEADER" < data.csv
```

---

### 7. เปิด Firewall

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 5432/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload

# ตรวจสอบ
sudo ufw status | grep 5432
```

---

### 8. ตั้งค่า PostgreSQL ให้รับ Connection จากภายนอก

```bash
# แก้ไข postgresql.conf (รับ connection จากทุก IP)
docker exec -it bjh_postgres bash -c \
  "echo \"listen_addresses = '*'\" >> /var/lib/postgresql/data/postgresql.conf"

# แก้ไข pg_hba.conf (อนุญาตให้ทุก IP connect ด้วย password)
docker exec -it bjh_postgres bash -c \
  "echo \"host all all 0.0.0.0/0 md5\" >> /var/lib/postgresql/data/pg_hba.conf"

# Restart container เพื่อให้การตั้งค่ามีผล
docker restart bjh_postgres

# รอ 5 วินาที
sleep 5

# ตรวจสอบว่า container ทำงานปกติ
docker ps | grep bjh_postgres
```

---

### 9. ทดสอบการเชื่อมต่อ

#### ทดสอบจาก Server เดียวกัน

```bash
# จาก server n8n.bjhbangkok.com
psql -h localhost -p 5432 -U postgres -d postgres
# หรือ
docker exec -it bjh_postgres psql -U postgres
```

#### ทดสอบจาก Local Machine

```bash
# จาก Windows (ใน PowerShell)
# ติดตั้ง psql ก่อน หรือใช้ pgAdmin
psql -h n8n.bjhbangkok.com -p 5432 -U postgres -d postgres

# Password: Bjh12345!!
```

#### ทดสอบด้วย Python

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="n8n.bjhbangkok.com",
        port=5432,
        user="postgres",
        password="Bjh12345!!",
        database="postgres"
    )
    print("✅ Connected successfully!")

    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    print(cursor.fetchone())

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

---

### 10. ตั้งค่าใน Railway

ไปที่ Railway Project → Variables → เพิ่ม:

```env
DB_HOST=n8n.bjhbangkok.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Bjh12345!!
DB_NAME=postgres
```

---

## 🔧 การจัดการ Container

### คำสั่งพื้นฐาน

```bash
# ดู container ทั้งหมด
docker ps -a

# หยุด container
docker stop bjh_postgres

# เริ่ม container
docker start bjh_postgres

# Restart container
docker restart bjh_postgres

# ดู logs
docker logs bjh_postgres
docker logs -f bjh_postgres  # real-time

# เข้าไปใน container
docker exec -it bjh_postgres bash

# ลบ container (ข้อมูลใน volume ยังอยู่)
docker rm -f bjh_postgres

# ลบทั้ง container และ volume (⚠️ ข้อมูลหาย!)
docker rm -f bjh_postgres
docker volume rm postgres_data
```

### Backup Database

```bash
# Backup ทั้ง database
docker exec bjh_postgres pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql

# Backup เฉพาะ schema
docker exec bjh_postgres pg_dump -U postgres -d postgres \
  --schema="BJH-Server" > backup_bjh_$(date +%Y%m%d).sql

# Backup แบบ compressed
docker exec bjh_postgres pg_dump -U postgres postgres | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Database

```bash
# Restore จาก SQL file
docker exec -i bjh_postgres psql -U postgres -d postgres < backup_20251117.sql

# Restore จาก compressed file
gunzip -c backup_20251117.sql.gz | docker exec -i bjh_postgres psql -U postgres -d postgres
```

---

## 🔒 ความปลอดภัย (Security)

### 1. เปลี่ยน Password

```bash
docker exec -it bjh_postgres psql -U postgres -c \
  "ALTER USER postgres WITH PASSWORD 'NewStrongPassword123!';"
```

### 2. จำกัด IP ที่เข้าถึงได้

```bash
# แก้ไข pg_hba.conf ให้รับเฉพาะ IP ที่ต้องการ
docker exec -it bjh_postgres bash

# แก้ไข file
vi /var/lib/postgresql/data/pg_hba.conf

# เปลี่ยนจาก:
# host all all 0.0.0.0/0 md5

# เป็น (Railway IP ranges):
# host all all 35.x.x.x/16 md5
# host all all 192.168.1.0/24 md5  # Local network

exit
docker restart bjh_postgres
```

### 3. ตั้งค่า SSL/TLS

```bash
# สร้าง self-signed certificate
docker exec -it bjh_postgres bash
cd /var/lib/postgresql/data

openssl req -new -x509 -days 365 -nodes -text \
  -out server.crt \
  -keyout server.key \
  -subj "/CN=n8n.bjhbangkok.com"

chmod 600 server.key
chown postgres:postgres server.key server.crt

# เปิด SSL ใน postgresql.conf
echo "ssl = on" >> postgresql.conf
echo "ssl_cert_file = 'server.crt'" >> postgresql.conf
echo "ssl_key_file = 'server.key'" >> postgresql.conf

exit
docker restart bjh_postgres
```

### 4. Firewall Rules (จำกัด IP)

```bash
# ลบ rule เดิม
sudo ufw delete allow 5432/tcp

# เพิ่ม rule ใหม่ (เฉพาะ Railway และ Local network)
sudo ufw allow from 192.168.1.0/24 to any port 5432
sudo ufw allow from 35.0.0.0/8 to any port 5432  # Railway IP range (ตรวจสอบจาก Railway docs)
```

---

## 📊 Monitoring

### ดูสถิติการใช้งาน

```bash
# เข้า psql
docker exec -it bjh_postgres psql -U postgres

-- ดู connections ปัจจุบัน
SELECT * FROM pg_stat_activity;

-- ดูขนาด database
SELECT pg_size_pretty(pg_database_size('postgres'));

-- ดูขนาด table
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'BJH-Server'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ดู slow queries
SELECT pid, age(clock_timestamp(), query_start), usename, query
FROM pg_stat_activity
WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY query_start DESC;
```

### Docker Stats

```bash
# ดูการใช้ resources
docker stats bjh_postgres

# แบบ snapshot
docker stats --no-stream bjh_postgres
```

---

## 🔄 Auto Backup (Cron Job)

```bash
# สร้าง backup script
cat > /home/user/backup_postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/user/postgres_backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup
docker exec bjh_postgres pg_dump -U postgres postgres | \
  gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# ลบ backup เก่าที่เก็บไว้เกิน 7 วัน
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
EOF

# ให้สิทธิ์ execute
chmod +x /home/user/backup_postgres.sh

# เพิ่ม cron job (backup ทุกวันเวลา 2:00 AM)
crontab -e

# เพิ่มบรรทัดนี้:
# 0 2 * * * /home/user/backup_postgres.sh >> /home/user/backup.log 2>&1
```

---

## ✅ Checklist

- [ ] รัน PostgreSQL container
- [ ] ตรวจสอบว่า container ทำงาน (`docker ps`)
- [ ] สร้าง schema และ table
- [ ] Import ข้อมูลจาก Local
- [ ] เปิด firewall port 5432
- [ ] ตั้งค่า PostgreSQL ให้รับ connection จากภายนอก
- [ ] Restart container
- [ ] ทดสอบเชื่อมต่อจาก Local machine
- [ ] ทดสอบเชื่อมต่อจาก Railway
- [ ] ตั้งค่า backup อัตโนมัติ
- [ ] ตั้งค่าความปลอดภัย (SSL, Firewall, Strong password)

---

## 🎉 เสร็จสิ้น!

ตอนนี้คุณมี PostgreSQL บน n8n.bjhbangkok.com แล้ว!

**Connection String:**

```
postgresql://postgres:Bjh12345!!@n8n.bjhbangkok.com:5432/postgres
```

**ใช้ใน Railway:**

```env
DB_HOST=n8n.bjhbangkok.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=Bjh12345!!
DB_NAME=postgres
```
