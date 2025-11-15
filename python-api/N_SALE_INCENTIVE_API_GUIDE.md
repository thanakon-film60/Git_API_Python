# คู่มือ API Google Sheet: N_SaleIncentive

## ภาพรวม

คู่มือนี้อธิบายวิธีการเชื่อมต่อกับ Google Sheet ชื่อ "N_SaleIncentive" เพื่อดึงข้อมูลรายรับของทีมขายมาแสดงในตาราง **"ประมาณการรายรับ"** ใน Performance Surgery Schedule Dashboard

---

## 📋 ข้อมูลที่ต้องใช้

### Google Sheet Information

- **Sheet Name**: `N_SaleIncentive`
- **Spreadsheet ID**: (ใช้ ID เดียวกับ "Film data" หรือระบุใหม่)

### Columns Mapping

| Column Name | ข้อมูลตัวอย่าง             | คำอธิบาย               | ใช้ในตาราง                  |
| ----------- | -------------------------- | ---------------------- | --------------------------- |
| `Sale`      | "จีน", "เจ", "ว่าน", "มุก" | ชื่อผู้ขาย/ผู้ติดต่อ   | ผู้ติดต่อ (Contact Person)  |
| `SaleDate`  | "2025-11-09 10:06:11"      | วันที่ขายได้ (รวมเวลา) | วันที่ (เอาเฉพาะวันเดือนปี) |
| `InCome`    | "10000", "25000"           | จำนวนรายรับ (บาท)      | ยอดรายรับ                   |

---

## 🔧 Python API Implementation

### 1. เพิ่ม Endpoint ใหม่ใน Python API (Railway)

สร้าง endpoint สำหรับดึงข้อมูลจาก sheet "N_SaleIncentive"

```python
# ใน main.py หรือ app.py
from datetime import datetime

@app.route('/api/sale-incentive', methods=['GET'])
def get_sale_incentive():
    """
    ดึงข้อมูลรายรับจาก N_SaleIncentive sheet
    """
    try:
        # เชื่อมต่อกับ Google Sheets
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        sheet = gc.open_by_key(spreadsheet_id)

        # เปิด worksheet ชื่อ "N_SaleIncentive"
        worksheet = sheet.worksheet('N_SaleIncentive')

        # ดึงข้อมูลทั้งหมด
        records = worksheet.get_all_records()

        # แปลงข้อมูลเป็นรูปแบบที่ใช้งานง่าย
        sale_data = []
        for record in records:
            try:
                # แปลง SaleDate จาก string เป็น date object
                sale_date_str = record.get('SaleDate', '')
                if sale_date_str:
                    # แยกเฉพาะวันที่ (ไม่เอาเวลา)
                    sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d %H:%M:%S').date()
                else:
                    continue  # ข้าม record ที่ไม่มีวันที่

                # ดึงข้อมูล Sale และ InCome
                sale_person = record.get('Sale', '').strip()
                income = float(record.get('InCome', 0))

                # เพิ่มข้อมูลลงใน list
                sale_data.append({
                    'sale_person': sale_person,
                    'sale_date': sale_date.isoformat(),  # Format: "2025-11-09"
                    'income': income,
                    'day': sale_date.day,
                    'month': sale_date.month,
                    'year': sale_date.year
                })
            except Exception as e:
                # ข้าม record ที่มีข้อมูลไม่ครบหรือ format ไม่ถูกต้อง
                print(f"Error processing record: {e}")
                continue

        return jsonify({
            'success': True,
            'data': sale_data,
            'total_records': len(sale_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sale-incentive/by-month', methods=['GET'])
def get_sale_incentive_by_month():
    """
    ดึงข้อมูลรายรับตามเดือนและปีที่กำหนด
    Query Parameters:
    - month: เดือน (1-12)
    - year: ปี (เช่น 2025)
    """
    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))

        # เชื่อมต่อกับ Google Sheets
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        sheet = gc.open_by_key(spreadsheet_id)
        worksheet = sheet.worksheet('N_SaleIncentive')
        records = worksheet.get_all_records()

        # กรองข้อมูลตามเดือนและปี
        filtered_data = []
        for record in records:
            try:
                sale_date_str = record.get('SaleDate', '')
                if not sale_date_str:
                    continue

                sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d %H:%M:%S').date()

                # ตรวจสอบว่าตรงกับเดือนและปีที่ต้องการหรือไม่
                if sale_date.month == month and sale_date.year == year:
                    sale_person = record.get('Sale', '').strip()
                    income = float(record.get('InCome', 0))

                    filtered_data.append({
                        'sale_person': sale_person,
                        'sale_date': sale_date.isoformat(),
                        'income': income,
                        'day': sale_date.day,
                        'month': sale_date.month,
                        'year': sale_date.year
                    })
            except Exception as e:
                continue

        return jsonify({
            'success': True,
            'data': filtered_data,
            'total_records': len(filtered_data),
            'month': month,
            'year': year
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## 🔗 Frontend Integration (Next.js/React)

### 2. สร้าง Utility Function สำหรับดึงข้อมูล

สร้างไฟล์ `src/utils/saleIncentiveApi.ts`

```typescript
// src/utils/saleIncentiveApi.ts

export interface SaleIncentiveData {
  sale_person: string;
  sale_date: string; // ISO format: "2025-11-09"
  income: number;
  day: number;
  month: number; // 1-12
  year: number;
}

/**
 * ดึงข้อมูลรายรับทั้งหมดจาก N_SaleIncentive sheet
 */
export async function fetchSaleIncentiveData(): Promise<SaleIncentiveData[]> {
  const pythonApiUrl =
    process.env.NEXT_PUBLIC_PYTHON_API_URL ||
    "https://believable-ambition-production.up.railway.app";

  try {
    const response = await fetch(`${pythonApiUrl}/api/sale-incentive`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || "Failed to fetch sale incentive data");
    }

    return result.data;
  } catch (error) {
    console.error("Error fetching sale incentive data:", error);
    throw error;
  }
}

/**
 * ดึงข้อมูลรายรับตามเดือนและปีที่กำหนด
 */
export async function fetchSaleIncentiveByMonth(
  month: number, // 0-11 (JavaScript month)
  year: number
): Promise<SaleIncentiveData[]> {
  const pythonApiUrl =
    process.env.NEXT_PUBLIC_PYTHON_API_URL ||
    "https://believable-ambition-production.up.railway.app";

  try {
    // แปลง JavaScript month (0-11) เป็น API month (1-12)
    const apiMonth = month + 1;

    const response = await fetch(
      `${pythonApiUrl}/api/sale-incentive/by-month?month=${apiMonth}&year=${year}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || "Failed to fetch sale incentive data");
    }

    return result.data;
  } catch (error) {
    console.error("Error fetching sale incentive by month:", error);
    throw error;
  }
}

/**
 * คำนวณรายรับรายวันตามผู้ติดต่อ
 * Returns: Map<ชื่อผู้ติดต่อ, Map<วันที่, รายรับรวม>>
 */
export function calculateDailyRevenueByPerson(
  data: SaleIncentiveData[],
  month: number, // 0-11
  year: number
): Map<string, Map<number, number>> {
  const revenueMap = new Map<string, Map<number, number>>();

  data.forEach((item) => {
    // ตรวจสอบว่าข้อมูลตรงกับเดือนและปีที่ต้องการหรือไม่
    if (item.month !== month + 1 || item.year !== year) {
      return;
    }

    const person = item.sale_person;
    const day = item.day;
    const income = item.income;

    // สร้าง Map สำหรับผู้ติดต่อถ้ายังไม่มี
    if (!revenueMap.has(person)) {
      revenueMap.set(person, new Map<number, number>());
    }

    const personMap = revenueMap.get(person)!;

    // บวกรายรับเข้าไปในวันนั้นๆ
    const currentRevenue = personMap.get(day) || 0;
    personMap.set(day, currentRevenue + income);
  });

  return revenueMap;
}

/**
 * แมพชื่อผู้ติดต่อกับ Row ID ในตาราง
 */
export const SALE_PERSON_TO_ROW_ID: { [key: string]: string } = {
  จีน: "105-จีน",
  มุก: "105-จีน", // มุกรวมกับจีน
  เจ: "107-เจ",
  ว่าน: "108-ว่าน",
};
```

---

## 📊 การใช้งานในตาราง "ประมาณการรายรับ"

### 3. อัพเดต Component `page.tsx`

เพิ่มการดึงข้อมูลจาก N_SaleIncentive และแสดงในตาราง

```typescript
// เพิ่ม import
import {
  fetchSaleIncentiveByMonth,
  calculateDailyRevenueByPerson,
  SaleIncentiveData,
  SALE_PERSON_TO_ROW_ID,
} from "@/utils/saleIncentiveApi";

// เพิ่ม state สำหรับข้อมูล Sale Incentive
const [saleIncentiveData, setSaleIncentiveData] = useState<SaleIncentiveData[]>(
  []
);
const [saleRevenueMap, setSaleRevenueMap] = useState<
  Map<string, Map<number, number>>
>(new Map());

// แก้ไข loadData function
const loadData = async (isManualRefresh = false) => {
  if (isManualRefresh) {
    setIsRefreshing(true);
  } else {
    setIsLoading(true);
  }
  setError(null);
  try {
    // Fetch surgery schedule data
    const surgeryData = await fetchSurgeryScheduleFromPythonAPI();
    setSurgeryData(surgeryData);

    // Fetch sale incentive data
    const saleData = await fetchSaleIncentiveByMonth(
      selectedMonth,
      selectedYear
    );
    setSaleIncentiveData(saleData);

    setLastUpdated(new Date());
  } catch (error: any) {
    setError(error.message || "เกิดข้อผิดพลาดในการโหลดข้อมูล");
  } finally {
    setIsLoading(false);
    setIsRefreshing(false);
  }
};

// อัพเดต useEffect สำหรับคำนวณ revenue map
useEffect(() => {
  if (saleIncentiveData.length > 0) {
    const newSaleRevenueMap = calculateDailyRevenueByPerson(
      saleIncentiveData,
      selectedMonth,
      selectedYear
    );
    setSaleRevenueMap(newSaleRevenueMap);
  }
}, [saleIncentiveData, selectedMonth, selectedYear]);

// แก้ไข getCellRevenue function เพื่อใช้ข้อมูลจาก N_SaleIncentive
const getCellRevenue = (day: number, rowId: string): number => {
  const contactPerson = CONTACT_PERSON_MAPPING[rowId];
  if (!contactPerson) return 0;

  // ใช้ข้อมูลจาก N_SaleIncentive แทนการคำนวณจาก surgery data
  if (rowId === "105-จีน") {
    const jinMap = saleRevenueMap.get("จีน");
    const mukMap = saleRevenueMap.get("มุก");

    const jinRevenue = jinMap?.get(day) || 0;
    const mukRevenue = mukMap?.get(day) || 0;

    return jinRevenue + mukRevenue;
  }

  const personMap = saleRevenueMap.get(contactPerson);
  if (!personMap) return 0;

  return personMap.get(day) || 0;
};
```

---

## 🚀 การ Deploy

### 4. Environment Variables

#### Railway (Python API)

ตรวจสอบว่ามี Environment Variables ครบถ้วน:

```
GOOGLE_SPREADSHEET_ID=<your-spreadsheet-id>
GOOGLE_SERVICE_ACCOUNT_EMAIL=<service-account-email>
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY=<private-key>
```

#### Vercel (Next.js Frontend)

```
NEXT_PUBLIC_PYTHON_API_URL=https://believable-ambition-production.up.railway.app
```

### 5. ทดสอบ API

#### Test Health Check

```bash
curl https://believable-ambition-production.up.railway.app/health
```

#### Test Sale Incentive Endpoint

```bash
# ดึงข้อมูลทั้งหมด
curl https://believable-ambition-production.up.railway.app/api/sale-incentive

# ดึงข้อมูลตามเดือน (พฤศจิกายน 2025)
curl "https://believable-ambition-production.up.railway.app/api/sale-incentive/by-month?month=11&year=2025"
```

---

## ✅ Checklist การตั้งค่า

- [ ] เพิ่ม sheet "N_SaleIncentive" ใน Google Spreadsheet
- [ ] ตรวจสอบว่า Service Account มีสิทธิ์เข้าถึง sheet
- [ ] เพิ่ม endpoint `/api/sale-incentive` ใน Python API
- [ ] เพิ่ม endpoint `/api/sale-incentive/by-month` ใน Python API
- [ ] สร้างไฟล์ `saleIncentiveApi.ts` ใน frontend
- [ ] อัพเดต `page.tsx` เพื่อใช้ข้อมูลจาก N_SaleIncentive
- [ ] Deploy Python API ไป Railway
- [ ] Deploy Frontend ไป Vercel
- [ ] ทดสอบ API endpoints
- [ ] ทดสอบตาราง "ประมาณการรายรับ" ใน frontend

---

## 📝 ข้อมูลเพิ่มเติม

### Format ของ SaleDate

- **Input**: `"2025-11-09 10:06:11"` (string)
- **Output**: `"2025-11-09"` (ISO date format, ไม่มีเวลา)

### การแมพผู้ติดต่อ

| Sale Name | Row ID   | แสดงในตารางเป็น |
| --------- | -------- | --------------- |
| จีน       | 105-จีน  | 105-จีน & มุก   |
| มุก       | 105-จีน  | 105-จีน & มุก   |
| เจ        | 107-เจ   | 107-เจ          |
| ว่าน      | 108-ว่าน | 108-ว่าน        |

### การคำนวณรายรับ

- รายรับจะถูกรวมตามวันที่และผู้ติดต่อ
- ถ้ามีหลายรายการในวันเดียวกัน จะบวกรวมกัน
- จีนและมุกจะรวมยอดเข้าด้วยกัน

---

## 🐛 Troubleshooting

### ปัญหา: ไม่พบ sheet "N_SaleIncentive"

**แก้ไข**: ตรวจสอบว่าชื่อ sheet ใน Google Spreadsheet ตรงกับที่กำหนดไว้

### ปัญหา: Date format ไม่ถูกต้อง

**แก้ไข**: ตรวจสอบว่า column "SaleDate" มี format: `YYYY-MM-DD HH:MM:SS`

### ปัญหา: InCome เป็น string แทน number

**แก้ไข**: ตรวจสอบว่า column "InCome" เป็นตัวเลข ไม่มีคำอื่นปนอยู่

---

## 📞 Support

หากมีปัญหาหรือคำถาม กรุณาตรวจสอบ:

1. Railway logs: https://railway.app/dashboard
2. Vercel logs: https://vercel.com/dashboard
3. Google Sheets API quota และ permissions
