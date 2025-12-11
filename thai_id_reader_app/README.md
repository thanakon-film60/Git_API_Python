# 🪪 Thai ID Card Reader System

ระบบอ่านบัตรประชาชนไทยสำหรับใช้กับ React/Next.js ผ่าน Railway Server

---

## 🏗️ สถาปัตยกรรม

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ระบบ Thai ID Card                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [เครื่องผู้ใช้]                [Railway Cloud]            [Next.js]    │
│  ┌─────────────────┐          ┌─────────────────┐        ┌──────────┐   │
│  │ ThaiIDAgent.exe │ ──POST──>│ /api/thaiid/    │ <─GET──│ เว็บของ  │   │
│  │                 │   ส่ง    │ receive         │   ดึง  │ คุณ      │   │
│  │ 1. เสียบเครื่อง │  ข้อมูล  │                 │  ข้อมูล│          │   │
│  │ 2. ใส่บัตร      │          │ /api/thaiid/    │        │          │   │
│  │ 3. กดสแกน       │          │ latest          │        │          │   │
│  └─────────────────┘          └─────────────────┘        └──────────┘   │
│         ↑                                                               │
│    เครื่องอ่าน USB GLINK                                                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 โครงสร้างไฟล์

```
thai_id_reader_app/
├── thai_id_agent.py         # 🖥️ โปรแกรมหลัก (ส่งข้อมูลไป Railway)
├── thai_id_reader.py        # โปรแกรม Local API (localhost:5051)
├── requirements.txt
├── build.bat
├── README.md
└── react/                   # 📦 ไฟล์สำหรับ Next.js
    ├── useThaiIDCard.ts     # ✅ Hook ดึงข้อมูลจาก Railway (แนะนำ)
    ├── ThaiIDCardDisplay.tsx # Component แสดงข้อมูลบัตร
    ├── useThaiIDReader.ts   # Hook เรียก localhost (ไม่แนะนำ)
    └── ThaiIDScanner.tsx    # Component เก่า
```

---

## 🚀 วิธีใช้งาน

### ขั้นตอนที่ 1: Build โปรแกรม .exe

```powershell
cd thai_id_reader_app

# ติดตั้ง dependencies
pip install flask pyscard requests pyinstaller

# Build เป็น .exe
pyinstaller --onefile --windowed --name="ThaiIDAgent" thai_id_agent.py
```

ไฟล์ `ThaiIDAgent.exe` จะอยู่ในโฟลเดอร์ `dist/`

### ขั้นตอนที่ 2: ใช้งานโปรแกรม

1. เสียบเครื่องอ่านบัตร GLINK USB
2. ใส่บัตรประชาชน
3. เปิดโปรแกรม `ThaiIDAgent.exe`
4. กดปุ่ม **"สแกนบัตรและส่งไป Railway"**

### ขั้นตอนที่ 3: นำไฟล์ไปใช้ใน Next.js

```
your-nextjs-project/
├── hooks/
│   └── useThaiIDCard.ts      # คัดลอกจาก react/useThaiIDCard.ts
└── components/
    └── ThaiIDCardDisplay.tsx  # คัดลอกจาก react/ThaiIDCardDisplay.tsx
```

---

## ⚛️ การใช้งานใน Next.js

### วิธีที่ 1: ใช้ Hook (แนะนำ)

```tsx
"use client";

import { useThaiIDCard } from "@/hooks/useThaiIDCard";

export default function RegistrationPage() {
  const { cardData, isLoading, error, fetchLatest, isDataAvailable } =
    useThaiIDCard({
      autoFetchInterval: 3000, // ตรวจสอบทุก 3 วินาที
      onDataReceived: (data) => {
        console.log("ได้รับข้อมูลใหม่:", data);
        // บันทึกลง database หรือทำอะไรก็ได้
      },
    });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">ลงทะเบียน</h1>

      {/* สถานะ */}
      <div className="mb-4">
        {isDataAvailable ? "✅ มีข้อมูล" : "⏳ รอข้อมูลจากเครื่องสแกน"}
      </div>

      {/* ปุ่มดึงข้อมูลด้วยตัวเอง */}
      <button
        onClick={fetchLatest}
        disabled={isLoading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {isLoading ? "กำลังโหลด..." : "🔄 ดึงข้อมูลล่าสุด"}
      </button>

      {/* Error */}
      {error && <p className="text-red-500 mt-2">{error}</p>}

      {/* แสดงข้อมูลบัตร */}
      {cardData && (
        <div className="mt-6 p-4 bg-gray-100 rounded-lg">
          <p className="text-2xl font-mono">{cardData.cid}</p>
          <p className="text-xl mt-2">{cardData.name?.th?.fullName}</p>
          <p>{cardData.name?.en?.fullName}</p>
          <p className="mt-2">วันเกิด: {cardData.birthDate}</p>
          <p>ที่อยู่: {cardData.address?.full}</p>
        </div>
      )}
    </div>
  );
}
```

### วิธีที่ 2: ใช้ Component สำเร็จรูป

```tsx
"use client";

import ThaiIDCardDisplay from "@/components/ThaiIDCardDisplay";

export default function Page() {
  return (
    <div className="max-w-lg mx-auto p-8">
      <ThaiIDCardDisplay
        autoRefresh={true}
        refreshInterval={3000}
        onDataReceived={(data) => {
          console.log("ได้รับข้อมูล:", data);
          // ส่งไป API ของคุณ
          fetch("/api/save-customer", {
            method: "POST",
            body: JSON.stringify(data),
          });
        }}
      />
    </div>
  );
}
```

### วิธีที่ 3: ใช้ fetch โดยตรง (Server Component / API Route)

```typescript
// app/api/get-latest-card/route.ts
import { NextResponse } from "next/server";

const RAILWAY_API = "https://believable-ambition-production.up.railway.app";

export async function GET() {
  const response = await fetch(`${RAILWAY_API}/api/thaiid/latest`);
  const data = await response.json();

  if (data.success) {
    return NextResponse.json(data.data);
  }

  return NextResponse.json({ error: "No data" }, { status: 404 });
}
```

---

## 📡 Railway API Endpoints

| Method | Endpoint              | คำอธิบาย                     |
| ------ | --------------------- | ---------------------------- |
| POST   | `/api/thaiid/receive` | รับข้อมูลจาก ThaiIDAgent.exe |
| GET    | `/api/thaiid/latest`  | ดึงข้อมูลบัตรล่าสุด          |
| GET    | `/api/thaiid/info`    | ข้อมูล API                   |

### Base URL

```
https://believable-ambition-production.up.railway.app
```

### ตัวอย่าง Response จาก `/api/thaiid/latest`

```json
{
  "success": true,
  "data": {
    "data": {
      "cid": "1-3098-01337-16-3",
      "cidRaw": "1309801337163",
      "name": {
        "th": {
          "title": "นาย",
          "firstName": "ธนากร",
          "lastName": "โฮงทอง",
          "fullName": "นาย ธนากร โฮงทอง"
        },
        "en": {
          "title": "Mr.",
          "firstName": "THANAKON",
          "lastName": "HONGTHONG",
          "fullName": "Mr. THANAKON HONGTHONG"
        }
      },
      "birthDate": "15/06/2541",
      "gender": "ชาย",
      "address": {
        "full": "123 หมู่ 4 ต.XXX อ.XXX จ.XXX"
      },
      "issueDate": "01/01/2563",
      "expireDate": "14/06/2571"
    },
    "timestamp": "2025-12-11T10:30:00",
    "source": "ThaiIDAgent"
  },
  "receivedAt": "2025-12-11T10:30:01"
}
```

---

## 🔧 Troubleshooting

### ❌ โปรแกรมไม่เจอเครื่องอ่านบัตร

- ตรวจสอบว่าเสียบ USB แล้ว
- ลองถอดแล้วเสียบใหม่
- ตรวจสอบใน Device Manager

### ❌ "Smart card is not responding"

- ใส่บัตรให้แน่น (chip ลงล่าง)
- ทำความสะอาด chip บนบัตร

### ❌ ส่งข้อมูลไป Railway ไม่สำเร็จ

- ตรวจสอบ internet connection
- ตรวจสอบว่า Railway server ทำงานอยู่

### ❌ Next.js ดึงข้อมูลไม่ได้

- ตรวจสอบว่าสแกนบัตรแล้ว
- ลองกด Refresh / รอ auto-refresh

---

## 📋 Requirements

**สำหรับ ThaiIDAgent.exe:**

- Windows 10/11
- เครื่องอ่านบัตร GLINK หรือเครื่องอ่านที่รองรับ PC/SC
- Internet connection

**สำหรับ Development:**

- Python 3.8+
- pyscard, flask, requests

---

## 📄 License

MIT License

---

## 👨‍💻 Developer

พัฒนาโดย **thanakon-film60**
