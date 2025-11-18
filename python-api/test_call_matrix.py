"""
ไฟล์สำหรับทดสอบ Call Matrix API
ใช้เมื่อตั้งค่า environment variables เรียบร้อยแล้ว
"""
import os
from dotenv import load_dotenv
from services.google_sheets import GoogleSheetsService
from services.call_matrix import CallMatrixService

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 ทดสอบ Call Matrix API")
print("=" * 60)

try:
    # ตรวจสอบ environment variables
    required_vars = [
        'GOOGLE_SPREADSHEET_ID',
        'GOOGLE_SERVICE_ACCOUNT_EMAIL',
        'GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ ไม่พบ Environment Variables: {', '.join(missing_vars)}")
        print("\n💡 กรุณาตั้งค่าใน .env หรือ Railway/Vercel environment variables")
        exit(1)
    
    print("✅ Environment variables พร้อมใช้งาน")
    print(f"📊 Spreadsheet ID: {os.getenv('GOOGLE_SPREADSHEET_ID')[:20]}...")
    print()
    
    # สร้าง service objects
    print("🔧 กำลังสร้าง service objects...")
    sheets_service = GoogleSheetsService()
    call_matrix_service = CallMatrixService(sheets_service)
    print("✅ สร้าง services สำเร็จ")
    print()
    
    # ทดสอบอ่านข้อมูล
    print("📖 กำลังอ่านข้อมูล Call Matrix...")
    result = call_matrix_service.get_call_matrix()
    
    if result.get('success'):
        print("✅ อ่านข้อมูลสำเร็จ!")
        print(f"📅 วันที่: {result.get('date')}")
        print(f"⏰ ช่วงเวลา: {len(result.get('time_slots', []))} ช่วง")
        print(f"👥 จำนวน Agents: {len(result.get('matrix_data', {}))}")
        print(f"📞 จำนวนการโทรทั้งหมด: {result.get('grand_total', 0)}")
        print()
        
        # แสดงข้อมูล Agents
        print("👥 รายชื่อ Agents:")
        for agent_id, total in result.get('totals_by_agent', {}).items():
            print(f"   - {agent_id}: {total} calls")
        print()
        
        # แสดงช่วงเวลา
        print("⏰ ช่วงเวลา:")
        for slot in result.get('time_slots', []):
            count = result.get('totals_by_slot', {}).get(slot, 0)
            print(f"   - {slot}: {count} calls")
        
    else:
        print("❌ เกิดข้อผิดพลาด:")
        print(f"   {result.get('error')}")
        if result.get('error_type') == 'sheet_not_found':
            print("\n💡 แนะนำ: ตรวจสอบชื่อ sheet ใน Google Sheets")
    
    print()
    print("=" * 60)
    print("✅ การทดสอบเสร็จสิ้น")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
    import traceback
    traceback.print_exc()
